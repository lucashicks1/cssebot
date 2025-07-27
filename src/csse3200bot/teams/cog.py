"""Teams cog."""

import logging

import discord
from discord import Role, app_commands
from discord.ext import commands

from csse3200bot.enums import CsseEnum

log = logging.getLogger(__name__)


class TeamEnum(CsseEnum):
    """Enum for team roles."""

    team1 = "Team 1"
    team2 = "Team 2"
    team3 = "Team 3"
    team4 = "Team 4"
    team5 = "Team 5"
    team6 = "Team 6"
    team7 = "Team 7"
    team8 = "Team 8"
    team9 = "Team 9"


class TeamsCog(commands.Cog):
    """Teams cog."""

    def __init__(self) -> None:
        """Constructor."""

    @app_commands.command()
    @app_commands.describe(team="Studio Team")
    async def assign(self, interaction: discord.Interaction, team: str) -> None:
        """Assign yourself to a team."""
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return

        member = guild.get_member(interaction.user.id)
        if member is None:
            await interaction.response.send_message("Member not found in this server.", ephemeral=True)
            return

        team_roles = await self._get_team_roles(interaction)

        role_to_assign = discord.utils.get(team_roles, name=team)
        if role_to_assign is None:
            await interaction.response.send_message(f"Team role '{team}' not found.", ephemeral=True)
            return

        # check if already has any team role
        member_team_roles = [role for role in member.roles if role in team_roles]

        if member_team_roles:
            existing_teams = ", ".join(r.name for r in member_team_roles)
            msg = (
                f"You've already been assigned to '{existing_teams}'."
                "Ask a tutor to remove it before assigning a new one."
            )
            await interaction.response.send_message(
                msg,
                ephemeral=True,
            )
            return

        # Assign the role
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

        return [r for r in guild.roles if r.name.startswith("Team")]

    @assign.autocomplete("team")
    async def assign_autocomplete(self, interaction: discord.Interaction, __: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for the 'set-repo' command."""
        return [
            app_commands.Choice(name=role.name, value=role.name) for role in await self._get_team_roles(interaction)
        ]
