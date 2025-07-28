"""App config module."""

from pydantic import Field
from pydantic_settings import BaseSettings

from csse3200bot.enums import LogLevel


class GeneralSettings(BaseSettings):
    """General app settings."""

    discord_bot_token: str = Field()
    db_url: str = Field()
    log_level: LogLevel = Field(default=LogLevel.debug)
    gh_token: str = Field()


CONFIG = GeneralSettings()  # type: ignore[call-arg]
