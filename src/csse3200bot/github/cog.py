"""GitHub Repository Cog."""

import logging
from collections.abc import Callable

import discord
from discord import app_commands
from github.Repository import Repository

from csse3200bot.bot import CSSEBot
from csse3200bot.cog import CSSECog
from csse3200bot.utils.collections import SyncCache

# Ref guide for Github Python Lib - https://pygithub.readthedocs.io/en/stable/reference.html

log = logging.getLogger(__name__)

REPO_CACHE_TTL = 300


class GitHubCog(CSSECog):
    """GitHub cog."""

    _repo_cache: SyncCache[str, Repository]

    def __init__(self, bot: CSSEBot) -> None:
        """Constructor."""
        super().__init__(bot)

        self._repo_cache = SyncCache[str, Repository](self._get_repo_wrapper())

    def _get_repo_wrapper(self) -> Callable[[str], Repository | None]:
        """A wrapper for getting a repo."""

        def fetch(repository_name: str) -> Repository | None:
            try:
                return self._bot.github_org.get_repo(repository_name)
            except Exception:
                log.exception(f"Couldn't find repo under '{repository_name}' name")
                return None

        return fetch

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
