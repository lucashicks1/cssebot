"""Teams cog."""

import logging

import discord
from discord import Role, app_commands

from csse3200bot.bot import CSSEBot
from csse3200bot.cog import CSSECog
from csse3200bot.teams.utils import get_member_team, get_team_roles

log = logging.getLogger(__name__)


class TeamsCog(CSSECog):
    """Teams cog."""

    def __init__(self, bot: CSSEBot) -> None:
        """Constructor."""
        super().__init__(bot)

    @app_commands.command()
    @app_commands.describe(team="Studio Team")
    async def set_team(self, interaction: discord.Interaction, team: str) -> None:
        """Assign yourself to a team."""
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return

        member = guild.get_member(interaction.user.id)
        if member is None:
            await interaction.response.send_message("Member not found in this server.", ephemeral=True)
            return

        current_team = get_member_team(member)
        if current_team:
            msg = (
                f"You've already been assigned to '{current_team.name}'."
                "Ask a tutor to remove it before assigning a new one."
            )
            await interaction.response.send_message(
                msg,
                ephemeral=True,
            )
            return

        team_roles = await self._get_team_roles(interaction)

        role_to_assign = discord.utils.get(team_roles, name=team)
        if role_to_assign is None:
            await interaction.response.send_message(f"Team role '{team}' not found.", ephemeral=True)
            return

        # assign the role
        try:
            await member.add_roles(role_to_assign, reason="User assigned self to a team via command")
            await interaction.response.send_message(f"You have been assigned to **{team}**.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permission to assign that role.", ephemeral=True)
        except Exception as e:
            msg = f"Error assigning role: {e}"
            log.exception(msg)
            await interaction.response.send_message("Something went wrong while assigning the role.", ephemeral=True)

    async def _get_team_roles(self, interaction: discord.Interaction) -> list[Role]:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return []

        return get_team_roles(guild)

    @set_team.autocomplete("team")
    async def assign_autocomplete(self, interaction: discord.Interaction, __: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for the 'set-repo' command."""
        return [
            app_commands.Choice(name=role.name, value=role.name) for role in await self._get_team_roles(interaction)
        ]
