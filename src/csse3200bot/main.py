"""Main module."""

import asyncio
import logging
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from discord.ext import commands
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from csse3200bot import constants
from csse3200bot.bot import CSSEBot
from csse3200bot.config import CONFIG
from csse3200bot.database.service import initialise_database
from csse3200bot.gh.cog import GitHubCog
from csse3200bot.greetings.cog import GreetingsCog
from csse3200bot.logger import configure_logging
from csse3200bot.studio.cog import StudioCog
from csse3200bot.teams.cog import TeamsCog

# Setting up the intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

log = logging.getLogger(__name__)

db_engine: AsyncEngine = create_async_engine(CONFIG.db_url, pool_pre_ping=True)
session_factory = async_sessionmaker(
    db_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

bot = CSSEBot(
    CONFIG.guild_ids, session_factory, constants.GH_ORG_NAME, CONFIG.gh_token, command_prefix="!", intents=intents
)


async def main() -> None:
    """Main function."""
    configure_logging()

    # Add the cogs
    cogs: list[commands.Cog] = [GitHubCog(bot), GreetingsCog(bot), StudioCog(bot), TeamsCog(bot)]
    for cog in cogs:
        log.info(f"Adding cog '{cog.__cog_name__} to bot'")
        await bot.add_cog(cog)

    await initialise_database(db_engine)

    try:
        await bot.start(CONFIG.discord_bot_token)
    except KeyboardInterrupt:
        log.info("Shutting down due to keyboard interrupt")
        await bot.close()
    finally:
        log.info("Disposing of db engine")
        await db_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
