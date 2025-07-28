"""Bot Module."""

import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

import discord
from discord.ext import commands
from github import Auth, Github
from github.Organization import Organization
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from csse3200bot.studio.models import StudioModel
from csse3200bot.studio.service import (
    create_studio,
    get_studio_by_details,
    get_studio_by_guild,
    link_guild_to_studio,
    unlink_guild,
)
from csse3200bot.utils.collections import AsyncCache

log = logging.getLogger(__name__)


class CSSEBot(commands.Bot):
    """Custom csse bot."""

    _sessionmaker: async_sessionmaker

    # Github stuff - yes I know, this ideally should be in cog, but used everywhere and referencing
    # cogs by strings is yuck!!!
    _org: Organization
    _gh_client: Github

    # studio info
    _studio_cache: AsyncCache[str, StudioModel]  # guild_id -> StudioModel

    def __init__(  # noqa: D107
        self,
        db_sessionmaker: async_sessionmaker,
        gh_org_name: str,
        gh_token: str,
        *args: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(*args, **kwargs)
        self._sessionmaker = db_sessionmaker

        self._gh_client = Github(auth=Auth.Token(gh_token))
        self._org = self._gh_client.get_organization(gh_org_name)

        self._studio_cache = AsyncCache(self._fetch_studio_by_guild_wrapper())

    # https://discordpy.readthedocs.io/en/stable/api.html#discord.Client.setup_hook
    # This is called when the bot starts
    async def setup_hook(self) -> None:
        """Setup."""
        log.info("Setup hook time.")
        # Setup the cogs -> I'm not a huge fan of registering them by name because things can get missed
        # But then if we do it inside, we've got to pass parameters through bot constructor!!!! - NOT NICE
        from csse3200bot.greetings.cog import GreetingsCog  # noqa: PLC0415
        from csse3200bot.repo.cog import RepoCog  # noqa: PLC0415
        from csse3200bot.studio.cog import StudioCog  # noqa: PLC0415
        from csse3200bot.teams.cog import TeamsCog  # noqa: PLC0415

        await self.add_cog(GreetingsCog())
        await self.add_cog(TeamsCog())
        await self.add_cog(StudioCog(self))
        await self.add_cog(RepoCog(self))

        synced_commands = await self.tree.sync()

        for com in synced_commands:
            msg = f"Synced '{com.name}' command"
            log.debug(msg)

        log.info(msg)

    @asynccontextmanager
    async def get_db(self) -> AsyncGenerator[AsyncSession]:
        """Get database session."""
        async with self._sessionmaker() as session:
            yield session

    def _fetch_studio_by_guild_wrapper(self) -> Callable[[str], Awaitable[StudioModel | None]]:
        """A wrapper for fetching a studio from a guild, to be used with the AsyncCache."""

        async def fetch(guild_id: str) -> StudioModel | None:
            async with self.get_db() as session:
                return await get_studio_by_guild(session, guild_id)

        return fetch

    async def get_studio(self, guild: discord.Guild) -> StudioModel | None:
        """Get studio from given guild, using the cache."""
        return await self._studio_cache.get(str(guild.id))

    async def create_or_update_studio(
        self,
        guild_id: str,
        studio_number: int,
        studio_year: int,
        repo_name: str,
    ) -> StudioModel:
        """Create or update studio ."""
        async with self.get_db() as session:
            # check if guild has studio
            existing_guild_studio = await get_studio_by_guild(session, guild_id)

            existing_studio = await get_studio_by_details(session, year=studio_year, number=studio_number)

            if not existing_studio:
                log.info(
                    f"Studio {studio_number} - {studio_year} does not exist, moving guild {guild_id} to that studio"
                )
                new_studio = await create_studio(session, studio_number, studio_year, repo_name)
                await unlink_guild(session, guild_id)
                await link_guild_to_studio(session, new_studio.studio_id, guild_id)
                self._studio_cache.set(guild_id, new_studio)
                return new_studio

            # Guild is not a part of a studio, but that studio does exist
            if not existing_guild_studio or existing_studio.studio_id != existing_guild_studio.studio_id:
                if not existing_guild_studio:
                    log.info("Guild doesn't have a studio, but the requested studio already exists")
                else:
                    log.info("Guild wants to join an already existing studio thats its not in")

                log.info(f"NOTE: Not updating studio {studio_number} - {studio_year} as guild is just joining")
                # NOT UPDATING INFO, IN CASE OF MISINPUT!!!
                await link_guild_to_studio(session, existing_studio.studio_id, guild_id)
                self._studio_cache.set(guild_id, existing_studio)
                return existing_studio

            # Otherwise same studio
            log.info("Guild wants to modify its own studio")
            new_studio = await create_studio(session, studio_number, studio_year, repo_name)
            self._studio_cache.set(guild_id, new_studio)
            return new_studio

    @property
    def github_org(self) -> Organization:
        """Github org property."""
        return self._org

    @property
    def github_client(self) -> Github:
        """Github client property."""
        return self._gh_client
