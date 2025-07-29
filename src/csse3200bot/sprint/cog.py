"""Sprint cog."""

import logging

from discord.ext import commands

from csse3200bot.bot import CSSEBot

log = logging.getLogger(__name__)


class SprintCog(commands.GroupCog, name="sprint"):
    """Sprint cog."""

    _bot: CSSEBot

    def __init__(self, bot: CSSEBot) -> None:
        """Constructor."""
        self._bot = bot
