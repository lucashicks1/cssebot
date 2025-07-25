"""App config module."""

from pydantic import Field
from pydantic_settings import BaseSettings


class GeneralSettings(BaseSettings):
    """General app settings."""

    discord_bot_token: str = Field()


CONFIG = GeneralSettings()  # type: ignore[call-arg]
