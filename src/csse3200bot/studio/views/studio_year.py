"""Studio year view."""

import datetime
import logging

import discord

from csse3200bot.studio.views import StudioSetupView, ValidationError

log = logging.getLogger(__name__)


def validate_studio_year(year_input: str) -> int:
    """Validate studio year input."""
    year_input = year_input.strip()

    if not year_input.isdigit():
        raise ValidationError("Year must be a number")

    year = int(year_input)
    current_year = datetime.datetime.now(tz=datetime.UTC).year

    if not (current_year - 5 <= year <= current_year):
        msg = f"Year must be between {current_year - 5} and {current_year}"
        raise ValidationError(msg)

    return year


class StudioYearSetupView(discord.ui.View):
    """Studio year setup."""

    def __init__(self, parent_view: StudioSetupView) -> None:
        """Constructor."""
        super().__init__(timeout=300)
        self.parent = parent_view
        self.add_item(StudioYearSelect(parent_view))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Checks the perms before doing the interaction."""
        return await self.parent.interaction_check(interaction)


class StudioYearSelect(discord.ui.Select):
    """Studio Year Select."""

    def __init__(self, parent_view: StudioSetupView) -> None:
        """Constructor."""
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
            year = validate_studio_year(self.values[0])
            self.parent.studio_year = year
            await self.parent.next_step(interaction)
        except ValidationError as e:
            await interaction.response.send_message(f"❌ {e!s}", ephemeral=True)
            await self.parent.retry_step(interaction)
        except Exception:
            msg = "Failed to validate studio year"
            log.exception(msg)
            await interaction.response.send_message(msg, ephemeral=True)
            await self.parent.retry_step(interaction)
