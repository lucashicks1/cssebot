"""Sprint services."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from csse3200bot.sprint.models import SprintFeatureModel


async def get_sprint_feature(
    session: AsyncSession, studio_id: UUID, team_id: str, sprint_number: int
) -> SprintFeatureModel | None:
    """Get a sprint features model."""
    stmt = select(SprintFeatureModel).where(
        SprintFeatureModel.studio_id == studio_id,
        SprintFeatureModel.team_id == team_id,
        SprintFeatureModel.sprint_number == sprint_number,
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def create_or_update_sprint_feature(
    session: AsyncSession,
    studio_id: UUID,
    team_id: str,
    sprint_number: int,
    features: str,
) -> SprintFeatureModel:
    """Create or update sprint features."""
    stmt = select(SprintFeatureModel).where(
        SprintFeatureModel.studio_id == studio_id,
        SprintFeatureModel.team_id == team_id,
        SprintFeatureModel.sprint_number == sprint_number,
    )
    result = await session.execute(stmt)
    existing = result.scalars().first()

    if existing:
        existing.features = features
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        return existing

    sprint_feature = SprintFeatureModel(
        studio_id=studio_id,
        team_id=team_id,
        sprint_number=sprint_number,
        features=features,
    )
    session.add(sprint_feature)
    await session.commit()
    await session.refresh(sprint_feature)
    return sprint_feature


async def get_features_for_sprint(
    session: AsyncSession,
    studio_id: UUID,
    sprint_number: int,
) -> list[SprintFeatureModel]:
    """Get sprint features."""
    stmt = select(SprintFeatureModel).where(
        SprintFeatureModel.studio_id == studio_id,
        SprintFeatureModel.sprint_number == sprint_number,
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
