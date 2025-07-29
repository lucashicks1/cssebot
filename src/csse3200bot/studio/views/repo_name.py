"""Studio repo name views."""

import logging
from typing import TYPE_CHECKING

import discord

from csse3200bot.studio.views.utils import manage_guild_perms_only

if TYPE_CHECKING:
    from csse3200bot.studio.views.setup import StudioSetupView

log = logging.getLogger(__name__)


class GitHubSetupView(discord.ui.View):
    """View that displays github repo picker."""

    def __init__(self, parent_view: "StudioSetupView", repo_names: list[str]) -> None:
        """Creates a github setup view, used when setting the github repo for a studio.

        Args:
            parent_view (StudioSetupView): studio setup view
            repo_names (list[str]): list of valid repo names for autocomplete
        """
        super().__init__(timeout=300)
        self.parent = parent_view
        self.add_item(GitHubRepoSelect(parent_view, repo_names))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Checks the perms before doing the interaction."""
        return await manage_guild_perms_only(interaction)


class GitHubRepoSelect(discord.ui.Select):
    """Github Repo Dropdown."""

    def __init__(self, parent_view: "StudioSetupView", repo_names: list[str]) -> None:
        """Dropdown for selecting github repo name.

        Args:
            parent_view (StudioSetupView): studio setup view
            repo_names (list[str]): list of valid repo names for autocomplete
        """
        self.parent = parent_view

        options = [discord.SelectOption(label=repo, value=repo) for repo in repo_names]

        super().__init__(
            placeholder="Select a Github repository name...",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Select callback."""
        try:
            selected_repo = self.values[0]
            self.parent.repo_name = selected_repo
            await self.parent.next_step(interaction)
        except Exception:
            msg = "Failed to select github repository"
            log.exception(msg)
            await interaction.response.send_message(msg, ephemeral=True)
            await self.parent.retry_step(interaction)
