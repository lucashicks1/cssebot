"""Database services/methods."""

import logging

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
)

log = logging.getLogger(__name__)


async def initialise_database(engine: AsyncEngine) -> None:
    """Initialise database."""
    # Importing as now sqlalchemy will know about them when creating the schema
    from csse3200bot.database.base import BaseDBModel  # noqa: PLC0415
    from csse3200bot.studio.models import StudioGuildModel, StudioModel  # noqa: F401, PLC0415

    async with engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.create_all)

    log.info("Initialising database was successful.")
