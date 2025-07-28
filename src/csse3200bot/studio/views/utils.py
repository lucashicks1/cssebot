"""View Utils."""

import logging

import discord

log = logging.getLogger(__name__)


async def manage_guild_perms_only(interaction: discord.Interaction) -> bool:
    """Ensure only users with Manage Guild permission can use setup."""
    member = interaction.user
    if isinstance(member, discord.User) or not member.guild_permissions.manage_guild:
        log.error(f"User from interaction should be a 'Member' and not a 'User' - {member}")
        await interaction.response.send_message(
            "❌ You need 'Manage Server' permissions to set up the bot for your studio.", ephemeral=True
        )
        return False
    return True


def make_step_embed(step: int, title: str, description: str, color: int = 0x7289DA) -> discord.Embed:
    """Makes step embed."""
    return discord.Embed(
        title=f"Step {step}: {title}",
        description=description,
        color=color,
    )
