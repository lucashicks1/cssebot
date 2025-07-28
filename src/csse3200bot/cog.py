"""Base cog module."""

import logging

from discord.ext import commands

from csse3200bot.bot import CSSEBot

# Ref guide for Github Python Lib - https://pygithub.readthedocs.io/en/stable/reference.html

log = logging.getLogger(__name__)

REPO_CACHE_TTL = 300


class CSSECog(commands.Cog):
    """Base cog."""

    _bot: CSSEBot

    def __init__(self, bot: CSSEBot) -> None:
        """Construct a base cog.

        Args:
            bot (CSSEBot): Reference to the main discord bot
        """
        self._bot = bot
