"""Teams cog."""

import logging
from typing import Literal

import discord
from discord import Role, app_commands
from discord.ext import commands

from csse3200bot import constants
from csse3200bot.bot import CSSEBot
from csse3200bot.studio.utils import studio_required
from csse3200bot.teams.service import create_or_update_sprint_feature, get_features_for_sprint
from csse3200bot.teams.utils import get_member_team, get_team_roles

log = logging.getLogger(__name__)

SprintNumber = Literal[1, 2, 3, 4]  # Need to find a better way to do this


class TeamsCog(commands.GroupCog, name="team"):
    """Teams cog."""

    _bot: CSSEBot

    def __init__(self, bot: CSSEBot) -> None:
        """Constructor."""
        self._bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Create team roles when bot joins a server."""
        await self._create_team_roles(guild)

    async def _create_team_roles(self, guild: discord.Guild) -> None:
        """Create the team roles if they don't exist."""
        team_names = [f"Team {i}" for i in range(1, constants.NUM_TEAMS + 1)]

        for team_name in team_names:
            # check if role exists
            existing_role = discord.utils.get(guild.roles, name=team_name)
            if existing_role:
                log.info(f"Role '{team_name}' already exists in guild '{guild.name}'")
                continue

            try:
                await guild.create_role(name=team_name, reason="Auto-created team role when bot joined server")
                log.info(f"Created role '{team_name}' in guild '{guild.name}'")
            except discord.Forbidden:
                log.exception(f"No permission to create role '{team_name}' in guild '{guild.name}'")
            except Exception:
                log.exception(f"Error creating role '{team_name}' in guild '{guild.name}'")

    @app_commands.command(name="assign")
    @app_commands.describe(team="Studio Team")
    async def assign_team(self, interaction: discord.Interaction, team: str) -> None:
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

    @assign_team.autocomplete("team")
    async def assign_autocomplete(self, interaction: discord.Interaction, __: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for the 'set-repo' command."""
        return [
            app_commands.Choice(name=role.name, value=role.name) for role in await self._get_team_roles(interaction)
        ]

    @app_commands.command(name="unassign")
    @app_commands.describe(member="User to unassign from a team")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def unassign_team(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """Unassign a user from a team."""
        team_role = get_member_team(member)

        if not team_role:
            await interaction.response.send_message(f"{member.display_name} is not in a team.", ephemeral=True)
            return

        try:
            await member.remove_roles(team_role, reason=f"Removed from team by staff ({interaction.user.name})")
            await interaction.response.send_message(
                f"{member.mention} has been removed from {team_role.name}.", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permission to remove that role.", ephemeral=True)
        except Exception as e:
            log.exception("Failed to remove team role")
            await interaction.response.send_message(f"Something went wrong: {e}", ephemeral=True)

    @app_commands.command(name="sprint_set", description="Set what features your team is completing for a given sprint")
    @app_commands.describe(
        sprint_number="Sprint in which you are completing the features", features="Features you are completing"
    )
    @studio_required
    async def sprint_set(self, interaction: discord.Interaction, sprint_number: SprintNumber, features: str) -> None:
        """Set what feature/s your team is doing for a given sprint."""
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Must be used in a server.", ephemeral=True)
            return

        member = interaction.user
        if not isinstance(member, discord.Member):
            await interaction.response.send_message("Must be used in a server.", ephemeral=True)
            return

        team_role = get_member_team(member)
        if team_role is None:
            await interaction.response.send_message("You must be in a team to use this command.", ephemeral=True)
            return

        studio = await self._bot.get_studio(guild)
        if studio is None:
            log.error("This should not occur as caught by 'studio_required' decorator")
            await interaction.response.send_message("Studio not fully setup yet", ephemeral=True)
            return

        async with self._bot.get_db() as session:
            await create_or_update_sprint_feature(
                session,
                studio_id=studio.studio_id,
                team_number=team_role.name,
                sprint_number=sprint_number,
                description=features,
            )
        await interaction.response.send_message(f"Updated features for **{team_role.name}** (Sprint {sprint_number}).")

    @app_commands.command(name="sprint_get", description="Get what features each team is working on for a given sprint")
    @app_commands.describe(sprint_number="Sprint in which you are completing the features")
    @studio_required
    async def sprint_get(self, interaction: discord.Interaction, sprint_number: SprintNumber) -> None:
        """Get what features each team is doing for a given sprint."""
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Must be used in a server.", ephemeral=True)
            return

        studio = await self._bot.get_studio(guild)
        if studio is None:
            log.error("This should not occur as caught by 'studio_required' decorator")
            await interaction.response.send_message("Studio not fully setup yet", ephemeral=True)
            return

        async with self._bot.get_db() as session:
            features = await get_features_for_sprint(session, studio.studio_id, sprint_number)

        if not features:
            await interaction.response.send_message(f"No teams have set features for sprint {sprint_number}.")
            return

        msg = f"**Sprint {sprint_number} Features**\n"
        for item in features:
            msg += f"- **{item.team_number}**: {item.description}\n"

        await interaction.response.send_message(msg)
