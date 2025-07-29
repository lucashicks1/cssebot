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
from csse3200bot.utils import AsyncCache

log = logging.getLogger(__name__)


@commands.command(name="sync_bot")
@commands.is_owner()
async def sync_command(ctx: commands.Context) -> None:
    """Sync Command."""
    guild = ctx.guild
    if guild is None:
        await ctx.send("Not allowed to be used outside of guild", ephemeral=True)
        return

    synced = await ctx.bot.tree.sync()

    for com in synced:
        log.info(f"Synced: {com}")

    await ctx.send(f"Synced {len(synced)} commands globally")


class CSSEBot(commands.Bot):
    """Custom csse bot."""

    _sessionmaker: async_sessionmaker
    _guilds: list[discord.abc.Snowflake]

    # Github stuff - yes I know, this ideally should be in cog, but used everywhere and referencing
    # cogs by strings is yuck!!!
    _org: Organization
    _gh_client: Github

    # studio info
    _studio_cache: AsyncCache[str, StudioModel]  # guild_id -> StudioModel

    def __init__(
        self,
        guild_ids: list[int],
        db_sessionmaker: async_sessionmaker,
        gh_org_name: str,
        gh_token: str,
        *args: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Creates a csse bot."""
        super().__init__(*args, **kwargs)
        self._guilds = [discord.Object(id=guild_id) for guild_id in guild_ids]
        self._sessionmaker = db_sessionmaker

        self._gh_client = Github(auth=Auth.Token(gh_token), per_page=100)
        self._org = self._gh_client.get_organization(gh_org_name)

        self._studio_cache = AsyncCache(self._fetch_studio_by_guild_wrapper())

    @asynccontextmanager
    async def get_db(self) -> AsyncGenerator[AsyncSession]:
        """Get database session."""
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                log.exception("Got a db error")
                await session.rollback()
                raise
            finally:
                await session.close()

    def _fetch_studio_by_guild_wrapper(self) -> Callable[[str], Awaitable[StudioModel | None]]:
        """A wrapper for fetching a studio from a guild, to be used with the AsyncCache."""

        async def fetch(guild_id: str) -> StudioModel | None:
            log.debug(f"Fetching studio for guild: {guild_id}")
            async with self.get_db() as session:
                result = await get_studio_by_guild(session, guild_id)
                log.debug(f" Result for guild {guild_id}: {result}")
                return result

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
