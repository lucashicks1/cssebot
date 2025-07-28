"""Views for studio."""

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

log = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error."""


class ViewStep(TypedDict):
    """View step."""

    title: str
    desc: str
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
                "desc": "What's your studio number?\n\n",
                "view_constructor": self._create_studio_num_view,
            },
            {
                "title": "Studio Year",
                "desc": f"What year is this studio for? (Defaults to {self._current_year})",
                "view_constructor": self._create_studio_year_view,
            },
            {
                "title": "GitHub Repo",
                "desc": "What's your GitHub repo name?\n\n",
                "view_constructor": self._create_repo_name_view,
            },
            {"title": "Confirm", "desc": "Confirm", "view_constructor": self._create_confirmation_view},
        ]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only users with Manage Guild permission can use setup."""
        member = interaction.user
        if isinstance(member, discord.User) or not member.guild_permissions.manage_guild:
            log.error(f"User from interaction should be a 'Member' and not a 'User' - {member}")
            await interaction.response.send_message(
                "❌ You need 'Manage Server' permissions to set up the bot for your studio.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Setup Studio", style=discord.ButtonStyle.primary)
    async def start_setup(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        """Start setup button."""
        await self.next_step(interaction)

    @staticmethod
    def _make_step_embed(step: int, title: str, description: str, color: int = 0x7289DA) -> discord.Embed:
        return discord.Embed(
            title=f"Step {step}: {title}",
            description=description,
            color=color,
        )

    def _create_studio_num_view(self) -> StudioNumberSetupView:
        return StudioNumberSetupView(self)

    def _create_studio_year_view(self) -> StudioYearSetupView:
        return StudioYearSetupView(self)

    def _create_repo_name_view(self) -> GitHubSetupView:
        return GitHubSetupView(self)

    def _create_confirmation_view(self) -> ConfirmationView:
        return ConfirmationView(self)

    async def retry_step(self, interaction: discord.Interaction) -> None:
        """Retry current step."""
        if self._current_step >= len(self._steps):
            await self.finish_setup(interaction)
            return

        step = self._steps[self._current_step]
        embed = self._make_step_embed(self._current_step + 1, step["title"], step["desc"])
        view = step["view_constructor"]()
        await interaction.response.edit_message(embed=embed, view=view)

    async def next_step(self, interaction: discord.Interaction) -> None:
        """Progress to the next step."""
        if self._current_step >= len(self._steps):
            await self.finish_setup(interaction)
            return

        try:
            step = self._steps[self._current_step]
            embed = self._make_step_embed(self._current_step + 1, step["title"], step["desc"])
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

    async def step_confirmation(self, interaction: discord.Interaction) -> None:
        """Confirmation step."""
        studio_number = self.studio_num or 0
        studio_year = self.studio_year or self._current_year
        github_repo = self.repo_name or "BLANK"

        display_name = f"Studio {studio_number} - {studio_year}"

        embed = discord.Embed(
            title="🎉 Your Studio Setup Summary",
            description=(
                f"**🎓 Studio:** {display_name}\n"
                f"**🔗 GitHub Repo Name:** [`{github_repo}`](https://github.com/{constants.GH_ORG_NAME}/{github_repo})\n\n"
            ),
            color=0x00FF00,
        )

        view = ConfirmationView(self)
        await interaction.response.edit_message(embed=embed, view=view)

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
                    "The bot is now ready and configured!\n\n"
                    f"**📚 Studio Configuration:**\n"
                    f"• Studio Number: {studio.studio_number}\n"
                    f"• GitHub Repo Name: {studio.repo_name}\n"
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
