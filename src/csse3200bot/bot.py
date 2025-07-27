"""Bot Module."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

log = logging.getLogger(__name__)


class CSSEBot(commands.Bot):
    """Custom csse bot."""

    _sessionmaker: async_sessionmaker

    # For cogs - not a fan of this pattern though
    _gh_token: str
    _gh_org_name: str

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

        self._gh_token = gh_token
        self._gh_org_name = gh_org_name

    # https://discordpy.readthedocs.io/en/stable/api.html#discord.Client.setup_hook
    # This is called when the bot starts
    async def setup_hook(self) -> None:
        """Setup."""
        log.info("Setup hook time.")
        # Setup the cogs -> I'm not a huge fan of registering them by name because things can get missed
        # But then if we do it inside, we've got to pass parameters through bot constructor!!!! - NOT NICE
        from csse3200bot.cogs.greetings import GreetingsCog  # noqa: PLC0415
        from csse3200bot.repo.cog import RepoCog  # noqa: PLC0415
        from csse3200bot.teams.cog import TeamsCog  # noqa: PLC0415

        await self.add_cog(GreetingsCog())
        await self.add_cog(TeamsCog())
        await self.add_cog(RepoCog(self, self._gh_org_name, self._gh_token))

        # Setup some internal state
        # Maybe the discord servers
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
