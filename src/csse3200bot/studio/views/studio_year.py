"""Studio year view."""

import datetime
import logging
from typing import TYPE_CHECKING

import discord

from csse3200bot.studio.views.utils import manage_guild_perms_only

if TYPE_CHECKING:
    from csse3200bot.studio.views.setup import StudioSetupView


log = logging.getLogger(__name__)


class StudioYearSetupView(discord.ui.View):
    """Studio year setup."""

    def __init__(self, parent_view: "StudioSetupView") -> None:
        """Creates view for studio year selection."""
        super().__init__(timeout=300)
        self.parent = parent_view
        self.add_item(StudioYearSelect(parent_view))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Checks the perms before doing the interaction."""
        return await manage_guild_perms_only(interaction)


class StudioYearSelect(discord.ui.Select):
    """Studio Year Select."""

    def __init__(self, parent_view: "StudioSetupView") -> None:
        """Creates a dropdown used to select the studio year."""
        self.parent = parent_view
        current_year = datetime.datetime.now(tz=datetime.UTC).year

        options = [
            discord.SelectOption(label=str(year), value=str(year)) for year in range(current_year, current_year - 6, -1)
        ]

        super().__init__(
            placeholder=f"Select the studio year (default: {current_year})",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Callback for select."""
        try:
            year = int(self.values[0])
            self.parent.studio_year = year
            await self.parent.next_step(interaction)
        except Exception:
            msg = "Failed to validate studio year"
            log.exception(msg)
            await interaction.response.send_message(msg, ephemeral=True)
            await self.parent.retry_step(interaction)
