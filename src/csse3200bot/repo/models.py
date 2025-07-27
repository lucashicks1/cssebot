"""Repo Models."""

from sqlalchemy.orm import Mapped, mapped_column

from csse3200bot.database.base import BaseDBModel


class RepoMappingModel(BaseDBModel):
    """DB Model for mapping github repositories to discord guilds/servers."""

    __tablename__ = "repo_mapping"

    guild_id: Mapped[str] = mapped_column(primary_key=True)
    # Could store the repo id but most of the github API uses the name
    repo_name: Mapped[str] = mapped_column(unique=True)
