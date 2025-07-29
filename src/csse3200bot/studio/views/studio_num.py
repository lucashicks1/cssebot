"""Studio number views."""

import logging
from typing import TYPE_CHECKING

import discord

from csse3200bot import constants
from csse3200bot.studio.views.utils import manage_guild_perms_only

if TYPE_CHECKING:
    from csse3200bot.studio.views.setup import StudioSetupView

log = logging.getLogger(__name__)


class StudioNumberSetupView(discord.ui.View):
    """View that displays the studio number setup."""

    def __init__(self, parent_view: "StudioSetupView") -> None:
        """Creates a view used during studio number selection.

        Args:
            parent_view (StudioSetupView): studio setup view.
        """
        super().__init__(timeout=300)
        self.add_item(StudioNumberSelect(parent_view))
        self.parent = parent_view

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Checks the perms before doing the interaction."""
        return await manage_guild_perms_only(interaction)


class StudioNumberSelect(discord.ui.Select):
    """Studio Number Dropdown."""

    def __init__(self, parent_view: "StudioSetupView") -> None:
        """Create a studio number dropdown.

        Args:
            parent_view (StudioSetupView): studio setup view.
        """
        self.parent = parent_view

        options = [discord.SelectOption(label=f"Studio {i}", value=str(i)) for i in range(1, constants.NUM_STUDIOS + 1)]

        super().__init__(
            placeholder="Choose your studio number...",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Select callback."""
        try:
            studio_number = int(self.values[0])
            self.parent.studio_num = studio_number
            await self.parent.next_step(interaction)
        except Exception:
            msg = "Failed to process studio number"
            log.exception(msg)
            await interaction.response.send_message(msg, ephemeral=True)
            await self.parent.retry_step(interaction)
