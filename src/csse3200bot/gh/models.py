"""Studio db models."""

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from csse3200bot.database.base import BaseDBModel
from csse3200bot.database.mixins import TimestampMixin


class DiscordUserModel(BaseDBModel, TimestampMixin):
    """DB Model for mapping discord ids to github name, etc."""

    __tablename__ = "discord_user"
    __table_args__ = (UniqueConstraint("gh_id"),)

    discord_user_id: Mapped[str] = mapped_column(primary_key=True)

    gh_id: Mapped[str | None]
