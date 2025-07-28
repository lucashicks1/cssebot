"""Studio repo name views."""

import logging
from typing import TYPE_CHECKING

import discord

from csse3200bot.studio.views.utils import manage_guild_perms_only

if TYPE_CHECKING:
    from csse3200bot.studio.views.setup import StudioSetupView

from csse3200bot.studio.views.utils import ViewDataValidationError

log = logging.getLogger(__name__)


class GitHubSetupView(discord.ui.View):
    """Github repo setup."""

    def __init__(self, parent_view: "StudioSetupView") -> None:  # noqa: D107
        super().__init__(timeout=300)
        self.parent = parent_view

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Checks the perms before doing the interaction."""
        return await manage_guild_perms_only(interaction)

    @discord.ui.button(label="Enter GitHub Repository Name", style=discord.ButtonStyle.primary, emoji="🔗")
    async def enter_github(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:  # noqa: D102
        modal = GitHubModal(self.parent)
        await interaction.response.send_modal(modal)


class GitHubModal(discord.ui.Modal):  # noqa: D101
    def __init__(self, parent_view: "StudioSetupView") -> None:  # noqa: D107
        super().__init__(title="GitHub Repository")
        self.parent = parent_view

        self.github_input: discord.ui.TextInput = discord.ui.TextInput(
            label="GitHub Repository",
            placeholder="username/repository or full GitHub URL",
            required=True,
            max_length=255,
        )
        self.add_item(self.github_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:  # noqa: D102
        try:
            self.parent.repo_name = self.github_input.value
            await self.parent.next_step(interaction)
        except ViewDataValidationError as e:
            await interaction.response.send_message(f"❌ {e!s}", ephemeral=True)
            await self.parent.retry_step(interaction)
