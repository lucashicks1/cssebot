"""Studio db models."""

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from csse3200bot.database.base import BaseDBModel
from csse3200bot.database.mixins import TimestampMixin


class StudioModel(BaseDBModel, TimestampMixin):
    """DB Model for mapping github repositories to discord guilds/servers."""

    __tablename__ = "studio"
    __table_args__ = (
        Index("ix_studio_number_year", "studio_number", "studio_year"),
        UniqueConstraint("studio_number", "studio_year"),
    )

    studio_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    studio_number: Mapped[int]
    studio_year: Mapped[int]
    repo_name: Mapped[str]  # Could store the repo id but most of the github API uses the name

    guild_links: Mapped[list["StudioGuildModel"]] = relationship(
        back_populates="studio", cascade="all, delete", lazy="joined"
    )


class StudioGuildModel(BaseDBModel):
    """Discord guild to studio link."""

    __tablename__ = "studio_guild"
    __table_args__ = (
        PrimaryKeyConstraint("studio_id", "guild_id"),
        Index("ix_studio_id_guild_id", "studio_id", "guild_id"),
    )

    studio_id: Mapped[str] = mapped_column(ForeignKey("studio.studio_id", ondelete="CASCADE"))
    guild_id: Mapped[str] = mapped_column()

    studio: Mapped[StudioModel] = relationship(back_populates="guild_links")
