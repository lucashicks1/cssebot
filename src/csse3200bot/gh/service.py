"""Github services."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from csse3200bot.gh.models import DiscordUserModel


async def get_user_model(session: AsyncSession, user_id: str) -> DiscordUserModel | None:
    """Get a discord user model."""
    return await session.get(DiscordUserModel, user_id)


async def get_user_model_by_gh(session: AsyncSession, gh_id: str) -> DiscordUserModel | None:
    """Get a discord user model by github name."""
    stmt = select(DiscordUserModel).where(
        DiscordUserModel.gh_id == gh_id,
    )
    result = await session.execute(stmt)
    return result.unique().scalar_one_or_none()


async def create_or_update_user_model(
    session: AsyncSession,
    user_id: str,
    gh_id: str | None,
) -> DiscordUserModel:
    """Create or update a discord user model."""
    existing = await session.get(DiscordUserModel, user_id)
    if existing:
        existing.gh_id = gh_id
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        return existing

    user_model = DiscordUserModel(discord_user_id=user_id, gh_id=gh_id)
    session.add(user_model)
    await session.commit()
    return user_model
