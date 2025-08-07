"""Studio service."""

import logging
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from csse3200bot.studio.models import StudioGuildModel, StudioModel

log = logging.getLogger(__name__)


async def link_guild_to_studio(session: AsyncSession, studio_id: UUID, guild_id: str) -> None:
    """Link a guild to a studio."""
    # remove existing
    await session.execute(delete(StudioGuildModel).where(StudioGuildModel.guild_id == guild_id))

    # add link
    session.add(StudioGuildModel(studio_id=studio_id, guild_id=guild_id))
    await session.commit()


async def unlink_guild(session: AsyncSession, guild_id: str) -> None:
    """Remove studio links for the given guild."""
    await session.execute(delete(StudioGuildModel).where(StudioGuildModel.guild_id == guild_id))
    await session.commit()


async def get_studio_by_guild(session: AsyncSession, guild_id: str) -> StudioModel | None:
    """Get the studio linked to the given guild."""
    log.debug("Preparing 'get-studio' query")
    stmt = select(StudioModel).join(StudioGuildModel).where(StudioGuildModel.guild_id == guild_id)
    log.debug("Executing query")
    result = await session.execute(stmt)
    log.debug(f"Got result - {result}")
    return result.unique().scalar_one_or_none()


async def get_studio_by_details(session: AsyncSession, year: int, number: int) -> StudioModel | None:
    """Get studio with year and number."""
    stmt = select(StudioModel).where(
        StudioModel.studio_year == year,
        StudioModel.studio_number == number,
    )
    result = await session.execute(stmt)
    return result.unique().scalar_one_or_none()


async def create_studio(
    session: AsyncSession,
    studio_number: int,
    studio_year: int,
    repo_name: str,
) -> StudioModel:
    """Creates new StudioModel in db."""
    data = {"repo": repo_name, "studio_num": studio_number, "studio_year": studio_year}
    log.debug(f"Creating studio {data}")

    new_studio = StudioModel(
        studio_number=studio_number,
        studio_year=studio_year,
        repo_name=repo_name,
    )
    session.add(new_studio)
    await session.commit()
    await session.refresh(new_studio)
    return new_studio


async def update_studio(
    session: AsyncSession,
    studio_model: StudioModel,
    repo_name: str,
) -> StudioModel:
    """Updates the repo_name and setup stats of studio."""
    if studio_model.repo_name == repo_name:
        return studio_model
    studio_model.repo_name = repo_name
    session.add(studio_model)
    await session.commit()
    await session.refresh(studio_model)
    return studio_model
