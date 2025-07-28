"""Sprint cog."""

import logging

from csse3200bot.bot import CSSEBot
from csse3200bot.cog import CSSECog

log = logging.getLogger(__name__)


class SprintCog(CSSECog):
    """Sprint cog."""

    def __init__(self, bot: CSSEBot) -> None:
        """Constructor."""
        super().__init__(bot)

    async def cog_load(self) -> None:
        """A special method that is called when the cog gets loaded - load the sprint features."""
