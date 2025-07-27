"""Code Repository Cog."""

import logging
import time

import discord
from discord import app_commands
from discord.ext import commands
from github import Auth, Github
from github.Organization import Organization
from github.Repository import Repository
from sqlalchemy import select

from csse3200bot.bot import CSSEBot
from csse3200bot.repo.models import RepoMappingModel

# Ref guide for Github Python Lib - https://pygithub.readthedocs.io/en/stable/reference.html

log = logging.getLogger(__name__)

REPO_CACHE_TTL = 300


class RepoCog(commands.Cog):
    """Repo cog."""

    _bot: CSSEBot
    _org: Organization
    _gh_client: Github

    _repos_ttl: float
    _repos: list[Repository]

    _repo_guild_map: dict[str, str]

    def __init__(self, bot: CSSEBot, org_name: str, github_token: str) -> None:
        """Constructor."""
        self._bot = bot
        auth = Auth.Token(github_token)
        self._gh_client = Github(auth=auth)

        self._org = self._gh_client.get_organization(org_name)

        # Repos
        self._repos = []
        self._repos_ttl = 0

        # Repo mapping
        self._repo_guild_map = {}

    async def cog_load(self) -> None:
        """A special method that is called when the cog gets loaded."""
        async with self._bot.get_db() as session:
            repo_mappings = (await session.execute(select(RepoMappingModel))).scalars().all()
            self._repo_guild_map = {mapping.guild_id: mapping.repo_name for mapping in repo_mappings}

    def is_repo_setup(self):  # noqa: ANN201
        """Discord check to see if discord repo has been selected."""

        def predicate(interaction: discord.Interaction) -> bool:
            return interaction.guild_id in self._repo_guild_map

        return app_commands.check(predicate)

    async def _get_repos_cached(self) -> list[Repository]:
        """Return cached repos, refresh if cache expired."""
        now = time.time()
        if now - self._repos_ttl > REPO_CACHE_TTL or not self._repos:
            # Refresh cache
            # Note: get_repos() returns a PaginatedList which is iterable but not a list,
            # so convert to list to cache.
            self._repos = list(self._org.get_repos())
            self._repos_ttl = now
        return self._repos

    async def _add_mapping(self, guild_id: str, repo_name: str) -> None:
        """Adds a mapping."""
        async with self._bot.get_db() as session:
            repo_mapping = RepoMappingModel(guild_id=guild_id, repo_name=repo_name)
            session.add(repo_mapping)
            await session.commit()
        self._repo_guild_map[guild_id] = repo_name

    @app_commands.command()
    @app_commands.describe(
        repo_name="Name of the servers github repository", replace="Whether to replace the current discord mapping"
    )
    async def set_repo(self, interaction: discord.Interaction, repo_name: str, replace: bool = False) -> None:  # noqa: FBT001, FBT002
        """Set the github repository that the server/studio will use."""
        repos = await self._get_repos_cached()
        if not any(r.name == repo_name for r in repos):
            await interaction.response.send_message(f"'{repo_name}' is not a valid repository!!!", ephemeral=True)
            return

        guild_id: str = str(interaction.guild_id)
        if not replace and guild_id in self._repo_guild_map:
            msg = (
                f"'{self._repo_guild_map[guild_id]}' repo is already mapped to this server"
                ", use the 'replace' paramter to replace the mapping"
            )
            await interaction.response.send_message(msg)
            return

        await self._add_mapping(guild_id, repo_name)
        await interaction.response.send_message(f"You have selected the '{repo_name}' repo", ephemeral=True)

    @set_repo.autocomplete("repo_name")
    async def set_repo_autocomplete(self, _: discord.Interaction, __: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for the 'set-repo' command."""
        repos = await self._get_repos_cached()
        return [app_commands.Choice(name=r.name, value=r.name) for r in repos]
