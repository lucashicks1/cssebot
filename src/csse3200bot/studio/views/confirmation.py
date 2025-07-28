"""Setup confirmation views."""

import logging
from typing import TYPE_CHECKING

import discord

from csse3200bot.studio.views.utils import manage_guild_perms_only

if TYPE_CHECKING:
    from csse3200bot.studio.views.setup import StudioSetupView

log = logging.getLogger(__name__)


class ConfirmationView(discord.ui.View):  # noqa: D101
    def __init__(self, parent_view: "StudioSetupView") -> None:  # noqa: D107
        super().__init__(timeout=300)
        self.parent = parent_view

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Checks the perms before doing the interaction."""
        return await manage_guild_perms_only(interaction)

    @discord.ui.button(label="Activate Studio Bot", style=discord.ButtonStyle.success, emoji="🚀")
    async def confirm_setup(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:  # noqa: D102
        await self.parent.finish_setup(interaction)
