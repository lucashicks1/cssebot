"""GitHub Repository Cog."""

import asyncio
import logging
from collections.abc import Awaitable, Callable

import discord
from discord import app_commands
from github.GithubException import GithubException
from github.Repository import Repository

from csse3200bot.bot import CSSEBot
from csse3200bot.cog import CSSECog
from csse3200bot.gh.models import DiscordUserModel
from csse3200bot.gh.service import create_or_update_user_model, get_user_model, get_user_model_by_gh
from csse3200bot.utils.collections import AsyncCache, SyncCache

# Ref guide for Github Python Lib - https://pygithub.readthedocs.io/en/stable/reference.html

log = logging.getLogger(__name__)

REPO_CACHE_TTL = 300


class GitHubCog(CSSECog):
    """GitHub cog."""

    # Repos
    _repo_cache: SyncCache[str, Repository]

    # Users
    _gh_users: dict[str, str]  # (name, id)
    _user_cache: AsyncCache[str, DiscordUserModel]

    def __init__(self, bot: CSSEBot) -> None:
        """Constructor."""
        super().__init__(bot)

        # Repos
        self._repo_cache = SyncCache[str, Repository](self._get_repo_wrapper())

        # Users
        self._gh_users = {}
        self._user_cache = AsyncCache[str, DiscordUserModel](self._get_user_wrapper())

    def _get_repo_wrapper(self) -> Callable[[str], Repository | None]:
        """A wrapper for getting a repo."""

        def fetch(repository_name: str) -> Repository | None:
            try:
                return self._bot.github_org.get_repo(repository_name)
            except GithubException:
                log.exception(f"Couldn't find repo under '{repository_name}' name")
                return None

        return fetch

    def _get_user_wrapper(self) -> Callable[[str], Awaitable[DiscordUserModel | None]]:
        """A wrapper for getting a user model."""

        async def fetch(user_id: str) -> DiscordUserModel | None:
            async with self._bot.get_db() as session:
                return await get_user_model(session, user_id)

        return fetch

    async def cog_load(self) -> None:
        """Load cog."""
        await super().cog_load()
        await self._load_members()

    async def _load_members(self) -> None:
        try:
            users = await asyncio.to_thread(self._bot.github_org.get_members)
            self._gh_users = {str(user.login): str(user.id) for user in users}
            log.info(f"Loaded {len(self._gh_users)} github users")
        except GithubException:
            log.exception("Couldn't find members for github org'")
            return

    @app_commands.command()
    async def set_gh(self, interaction: discord.Interaction, gh_username: str) -> None:
        """Associate your discord user with a github user."""
        await interaction.response.defer()
        if gh_username not in self._gh_users:
            await interaction.followup.send(
                f"The github user {gh_username} chosen doesn't exist, ask the tutors to reload the cached users if this is a mistake",  # noqa: E501
                ephemeral=True,
            )
            return

        user_id: str = str(interaction.user.id)
        gh_user_id = self._gh_users[gh_username]

        existing = await self._user_cache.get(user_id)
        existing_gh: DiscordUserModel | None
        async with self._bot.get_db() as session:
            existing_gh = await get_user_model_by_gh(session, gh_user_id)

        # trying to set the same github user
        if existing_gh is not None and existing_gh.discord_user_id == user_id:
            log.info("Same github user selected")
            await interaction.followup.send("You are already associated with that github user", ephemeral=True)
            return

        # Github user is already linked
        if existing_gh is not None:
            log.info("Github user is already linked")
            gh_holder = self._bot.get_user(int(existing_gh.discord_user_id))
            if gh_holder is not None:
                await interaction.followup.send(
                    f"That github user is already associated with {gh_holder.mention}", ephemeral=True
                )
                return

            # They don't exist in the server anymore
            await interaction.followup.send(
                "That github user is associated with a user who has left - unsetting them now, try again in a bit",
                ephemeral=True,
            )
            async with self._bot.get_db() as session:  # opening this again is yuck
                await create_or_update_user_model(session, existing_gh.discord_user_id, None)
            return

        # they've already got a github user set
        if existing is not None and existing.gh_id is not None:
            log.info("Github user is already set")
            await interaction.followup.send(
                "You already are associated to a github account, ask staff to unset it for you", ephemeral=True
            )
            return

        # At this point, user doesn't have github and no one has got that account yet
        async with self._bot.get_db() as session:  # opening this again is yuck
            await create_or_update_user_model(session, user_id, gh_user_id)
        await interaction.followup.send(f"You have now set your github account to '{gh_username}'.", ephemeral=True)

    @app_commands.command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def unset_gh(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """Unassociate a discord user with a github user - Staff Only."""
        await interaction.response.defer()
        user_id: str = str(member.id)
        model = await self._user_cache.get(user_id)
        if model is None:
            await interaction.followup.send(f"{member.mention} hasn't got anything set up yet.", ephemeral=True)
            return

        if model.gh_id is None:
            await interaction.followup.send(
                f"User '{member.mention}' hasn't got a github user associated with them.", ephemeral=True
            )
            return

        async with self._bot.get_db() as session:
            result = await create_or_update_user_model(session, user_id, None)
            self._user_cache.set(user_id, result)
        await interaction.followup.send(f"{member.mention}'s has been unassociated from a github user.", ephemeral=True)

    @app_commands.command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def refresh_gh_names(self, interaction: discord.Interaction) -> None:
        """Refreshes the cache of github usernames - useful if students just joined and can't find their name to set."""
        await interaction.response.defer()
        log.info("Got a 'refresh_gh_names command'")
        await self._load_members()
        await interaction.followup.send("All github members in the org have been refreshed", ephemeral=True)

    @app_commands.command()
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id))
    async def repo_info(self, interaction: discord.Interaction) -> None:
        """Get information about your studio's repository."""
        guild = interaction.guild
        if guild is None:
            msg = "Get Repo command must be used in a guild"
            log.warning(msg)
            await interaction.response.send_message(msg, ephemeral=True)
            return

        studio = await self._bot.get_studio(guild)
        if studio is None:
            msg = "Can't use this command until the studio is setup with the bot"
            await interaction.response.send_message(msg, ephemeral=True)
            return

        repo = self._repo_cache.get(studio.repo_name)
        if repo is None:
            msg = f"Unable to find repository '{studio.repo_name}' in github org"
            await interaction.response.send_message(msg, ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{repo.full_name}",
            url=repo.html_url,
            description=repo.description or "No description provided.",
            color=discord.Color.blue(),
        )

        embed.add_field(name="⭐ Stars", value=str(repo.stargazers_count), inline=True)
        embed.add_field(name="🍴 Forks", value=str(repo.forks_count), inline=True)
        embed.add_field(name="👀 Watchers", value=str(repo.subscribers_count), inline=True)
        embed.add_field(name="🧑‍💻 Open Issues", value=str(repo.open_issues_count), inline=True)
        embed.add_field(name="📅 Created At", value=discord.utils.format_dt(repo.created_at, style="D"), inline=True)
        embed.add_field(name="🛠 Updated At", value=discord.utils.format_dt(repo.updated_at, style="R"), inline=True)

        # This should always be true
        if repo.organization and repo.organization.avatar_url:
            embed.set_thumbnail(url=repo.organization.avatar_url)

        await interaction.response.send_message(embed=embed)

    @repo_info.error
    async def on_repo_info_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        """On error for repo info command."""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error), ephemeral=True)
