"""Teams models."""

from uuid import UUID

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from csse3200bot.database.base import BaseDBModel


class TeamSprintModel(BaseDBModel):
    """DB Model for tracking what teams are doing what sprints."""

    __tablename__ = "sprint_features"
    __table_args__ = (PrimaryKeyConstraint("studio_id", "team_number", "sprint_number"),)

    studio_id: Mapped[UUID] = mapped_column(ForeignKey("studio.studio_id", ondelete="CASCADE"))
    team_number: Mapped[str]
    sprint_number: Mapped[int]
    description: Mapped[str]
