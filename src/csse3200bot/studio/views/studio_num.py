"""Studio number views."""

import logging

import discord

from csse3200bot import constants
from csse3200bot.studio.views import StudioSetupView, ValidationError

log = logging.getLogger(__name__)


def validate_studio_number(studio_input: str) -> int:
    """Validate studio number input."""
    studio_input = studio_input.strip()

    if not studio_input.isdigit():
        raise ValidationError("Studio number must be a positive number")

    studio_num = int(studio_input)

    if studio_num < 1:
        raise ValidationError("Studio number must be greater than 0")
    if studio_num > 999:  # noqa: PLR2004
        raise ValidationError("Studio number must be less than 1000")

    return studio_num


class StudioNumberSetupView(discord.ui.View):
    """View that displays the studio number setup."""

    def __init__(self, parent_view: "StudioSetupView") -> None:  # noqa: D107
        super().__init__(timeout=300)
        self.add_item(StudioNumberSelect(parent_view))
        self.parent = parent_view

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Checks the perms before doing the interaction."""
        return await self.parent.interaction_check(interaction)


class StudioNumberSelect(discord.ui.Select):
    """Studio Number Dropdown."""

    def __init__(self, parent_view: StudioSetupView) -> None:  # noqa: D107
        self.parent = parent_view

        options = [discord.SelectOption(label=f"Studio {i}", value=str(i)) for i in range(1, constants.NUM_STUDIOS)]

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
