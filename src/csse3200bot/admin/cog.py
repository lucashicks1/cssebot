"""Admin cofg."""

import logging

import discord
from discord import app_commands

from csse3200bot.bot import CSSEBot
from csse3200bot.cog import CSSECog

log = logging.getLogger(__name__)


class AdminCog(CSSECog):
    """Admin cog cog."""

    def __init__(self, bot: CSSEBot) -> None:
        """Constructor."""
        super().__init__(bot)

    async def cog_load(self) -> None:
        """A special method that is called when the cog gets loaded - load the sprint features."""

    @app_commands.command(description="Sync the bot")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def sync_bot(self, interaction: discord.Interaction) -> None:
        """Sync the bot."""
        log.debug("Got a 'sync' command")
        num_synced = await self._bot.sync()
        await interaction.response.send_message(f"Successfully synced {num_synced} command(s).", ephemeral=True)
