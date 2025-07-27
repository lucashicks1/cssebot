"""Bot Module."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from csse3200bot.cogs.greetings import GreetingsCog


class DiscordBot(commands.Bot):
    """Custom csse bot."""

    _sessionmaker: async_sessionmaker

    def __init__(self, db_sessionmaker: async_sessionmaker, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401, D107
        super().__init__(*args, **kwargs)
        self._sessionmaker = db_sessionmaker

    # https://discordpy.readthedocs.io/en/stable/api.html#discord.Client.setup_hook
    # This is called when the bot starts
    async def setup_hook(self) -> None:
        """Setup."""
        # Setup the cogs -> I'm not a huge fan of registering them by name because things can get missed
        await self.add_cog(GreetingsCog())

        # Setup some internal state
        # Maybe the discord servers
        await self.tree.sync()

    @asynccontextmanager
    async def get_db(self) -> AsyncGenerator[AsyncSession]:
        """Get database session."""
        async with self._sessionmaker() as session:
            yield session
