"""Views for studio setup."""

import datetime
import logging
from collections.abc import Callable
from typing import TypedDict

import discord

from csse3200bot import constants
from csse3200bot.bot import CSSEBot
from csse3200bot.studio.views.confirmation import ConfirmationView
from csse3200bot.studio.views.repo_name import GitHubSetupView
from csse3200bot.studio.views.studio_num import StudioNumberSetupView
from csse3200bot.studio.views.studio_year import StudioYearSetupView
from csse3200bot.studio.views.utils import make_step_embed, manage_guild_perms_only

log = logging.getLogger(__name__)


class ViewStep(TypedDict):
    """View step."""

    title: str
    desc: Callable[[], str]
    view_constructor: Callable[[], discord.ui.View]


class StudioSetupView(discord.ui.View):
    """Studio setup view for collecting studio configuration."""

    _bot: CSSEBot
    _guild: discord.Guild

    _current_step: int
    _steps: list[ViewStep]

    _current_year: int

    studio_num: int | None
    studio_year: int | None
    repo_name: str | None

    def __init__(self, bot: CSSEBot, guild: discord.Guild) -> None:
        """Constructor."""
        super().__init__(timeout=600)
        self._bot = bot
        self._guild = guild

        self.studio_num = None
        self.studio_year = datetime.datetime.now(tz=datetime.UTC).year
        self.repo_name = None

        self._current_year = datetime.datetime.now(tz=datetime.UTC).year

        self._current_step = 0

        self._steps = [
            {
                "title": "Studio Number",
                "desc": lambda: "What's your studio number?\n\n",
                "view_constructor": lambda: StudioNumberSetupView(self),
            },
            {
                "title": "Studio Year",
                "desc": lambda: f"What year is this studio for? (Defaults to {self._current_year})",
                "view_constructor": lambda: StudioYearSetupView(self),
            },
            {
                "title": "GitHub Repo",
                "desc": lambda: "What's your GitHub repo?\n\n",
                "view_constructor": lambda: GitHubSetupView(
                    self, [repo.name for repo in self._bot.github_org.get_repos()]
                ),
            },
            {
                "title": "Confirm",
                "desc": lambda: (
                    f"**Studio Number:** {self.studio_num}\n"
                    f"**Studio Year:** {self.studio_year}\n"
                    f"**GitHub Repo:** [`{self.repo_name}`](https://github.com/{constants.GH_ORG_NAME}/{self.repo_name})\n\n"
                ),
                "view_constructor": lambda: ConfirmationView(self),
            },
        ]

    @discord.ui.button(label="Setup Studio", style=discord.ButtonStyle.primary)
    async def start_setup(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        """Start setup button."""
        await self.next_step(interaction)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Checks the perms before doing the interaction."""
        return await manage_guild_perms_only(interaction)

    async def retry_step(self, interaction: discord.Interaction) -> None:
        """Retry current step."""
        if self._current_step >= len(self._steps):
            await self.finish_setup(interaction)
            return

        step = self._steps[self._current_step]
        embed = make_step_embed(self._current_step + 1, step["title"], step["desc"]())
        view = step["view_constructor"]()
        await interaction.response.edit_message(embed=embed, view=view)

    async def next_step(self, interaction: discord.Interaction) -> None:
        """Progress to the next step."""
        if self._current_step >= len(self._steps):
            await self.finish_setup(interaction)
            return

        try:
            step = self._steps[self._current_step]
            embed = make_step_embed(self._current_step + 1, step["title"], step["desc"]())
            view = step["view_constructor"]()
            await interaction.response.edit_message(embed=embed, view=view)

            self._current_step += 1
        except Exception:
            log.exception("Error executing step")
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="Setup Error",
                    description="An unexpected error occurred during setup. Please try again.",
                    color=0xFF0000,
                ),
                view=None,
            )
            self.stop()

    async def finish_setup(self, interaction: discord.Interaction) -> None:
        """Save configuration using the view."""
        try:
            if self.studio_num is None or self.repo_name is None or self.studio_year is None:
                embed = discord.Embed(
                    title="❌ Setup Failed",
                    description="There was an error saving your studio configuration - studio num/year/repo name failed",  # noqa: E501
                    color=0xFF0000,
                )
                await interaction.response.edit_message(embed=embed, view=None)
                return

            guild_id: str = str(interaction.guild_id)
            studio = await self._bot.create_or_update_studio(
                guild_id, self.studio_num, self.studio_year, self.repo_name
            )

            embed = discord.Embed(
                title="🎉 Studio Setup Complete!",
                description=(
                    f"**Welcome to Studio {studio.studio_number} - {studio.studio_year}!** 🎓\n\n"
                    "The bot is now ready to go!\n\n"
                    f"• Studio Number: {studio.studio_number}\n"
                    f"• Studio Year: {studio.studio_year}\n"
                    f"• GitHub Repo Name: {studio.repo_name}\n"
                    f"• Updated At: {studio.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                    f"• Created At: {studio.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                ),
                color=0x00FF00,
            )

            await interaction.response.edit_message(embed=embed, view=None)
            msg = f"Studio setup completed for guild {guild_id} - Studio {studio.studio_number} - {studio.studio_year}"
            log.info(msg)

        except Exception:
            log.exception(f"Failed to save studio setup for guild {guild_id}")
            embed = discord.Embed(
                title="❌ Setup Failed",
                description="There was an error saving your studio configuration. Please try again.",
                color=0xFF0000,
            )
            await interaction.response.edit_message(embed=embed, view=None)

        self.stop()
