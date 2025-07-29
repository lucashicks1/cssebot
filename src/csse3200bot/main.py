"""Main module."""

import asyncio
import logging

import discord
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
from csse3200bot.logger import configure_logging

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
