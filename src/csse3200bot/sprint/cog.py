"""Sprint cog."""

import logging

from discord.ext import commands

from csse3200bot.bot import CSSEBot

log = logging.getLogger(__name__)


class SprintCog(commands.Cog):
    """Sprint cog."""

    _bot: CSSEBot

    def __init__(self, bot: CSSEBot) -> None:
        """Constructor."""
        self._bot = bot

    async def cog_load(self) -> None:
        """A special method that is called when the cog gets loaded - load the sprint features."""
