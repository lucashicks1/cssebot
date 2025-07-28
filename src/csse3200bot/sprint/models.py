"""DB Models for sprint-related discord bits."""

from uuid import UUID

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from csse3200bot.database.base import BaseDBModel


class SprintFeatureModel(BaseDBModel):
    """DB Model for tracking what teams are doing what features."""

    __tablename__ = "sprint_features"
    __table_args__ = (PrimaryKeyConstraint("studio_id", "team_id", "sprint_number"),)

    studio_id: Mapped[UUID] = mapped_column(ForeignKey("studio.studio_id", ondelete="CASCADE"))
    team_id: Mapped[str]  # team identifier string
    sprint_number: Mapped[int]
    features: Mapped[str]  # JSON string or serialized features
