"""Team Sprint services."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from csse3200bot.teams.models import TeamSprintModel


async def get_sprint_feature(
    session: AsyncSession, studio_id: UUID, team_number: str, sprint_number: int
) -> TeamSprintModel | None:
    """Get a sprint features model."""
    stmt = select(TeamSprintModel).where(
        TeamSprintModel.studio_id == studio_id,
        TeamSprintModel.team_number == team_number,
        TeamSprintModel.sprint_number == sprint_number,
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def create_or_update_sprint_feature(
    session: AsyncSession,
    studio_id: UUID,
    team_number: str,
    sprint_number: int,
    description: str,
) -> TeamSprintModel:
    """Create or update sprint features."""
    stmt = select(TeamSprintModel).where(
        TeamSprintModel.studio_id == studio_id,
        TeamSprintModel.team_number == team_number,
        TeamSprintModel.sprint_number == sprint_number,
    )
    result = await session.execute(stmt)
    existing = result.scalars().first()

    if existing:
        existing.description = description
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        return existing

    sprint_feature = TeamSprintModel(
        studio_id=studio_id,
        team_number=team_number,
        sprint_number=sprint_number,
        description=description,
    )
    session.add(sprint_feature)
    await session.commit()
    await session.refresh(sprint_feature)
    return sprint_feature


async def get_features_for_sprint(
    session: AsyncSession,
    studio_id: UUID,
    sprint_number: int,
) -> list[TeamSprintModel]:
    """Get sprint features."""
    stmt = select(TeamSprintModel).where(
        TeamSprintModel.studio_id == studio_id,
        TeamSprintModel.sprint_number == sprint_number,
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
