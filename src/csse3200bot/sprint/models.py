"""DB Models for sprint-related discord bits."""

from sqlalchemy.orm import Mapped, mapped_column

from csse3200bot.database.base import BaseDBModel


class SprintFeatureModel(BaseDBModel):
    """DB Model for tracking what teams are doing what features."""

    __tablename__ = "sprint_features"

    studio: Mapped[int] = mapped_column(primary_key=True)
    team: Mapped[str] = mapped_column(primary_key=True)
    sprint: Mapped[int] = mapped_column(primary_key=True)
    features: Mapped[str]
