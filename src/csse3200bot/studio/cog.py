"""Studio cog."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from csse3200bot.bot import CSSEBot
from csse3200bot.studio.views import StudioSetupView

log = logging.getLogger(__name__)


class StudioCog(commands.Cog):
    """Studio management and setup cog."""

    _bot: CSSEBot

    def __init__(self, bot: CSSEBot) -> None:
        """Constructor."""
        self._bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Triggered when bot joins a new server."""
        log.info(f"Joined guild: {guild.name} (ID: {guild.id})")

        studio = await self._bot.get_studio(guild)
        if studio is not None:
            log.info(f"Studio already setup for guild {guild.id}")
            return

        # Find suitable channel for setup message
        setup_channel = None
        for channel in guild.text_channels:
            perms = channel.permissions_for(guild.me)
            log.debug(f"Checking channel {channel.name} perms: {perms.send_messages}")
            if channel.permissions_for(guild.me).send_messages:
                setup_channel = channel
                break

        if not setup_channel:
            log.warning(f"No suitable channel found in {guild.name}")
            return

        # welcome message
        embed = discord.Embed(
            title="Welcome to CSSE Bot!",
            description=(f"Thanks for adding me to **{guild.name}**!\n\n"),
            color=0x7289DA,
        )
        embed.set_footer(text="Click the button below to begin setup")

        try:
            view = StudioSetupView(self._bot, guild)
        except Exception:
            log.exception("Error creating StudioSetupView")

        try:
            log.debug("Attempting to send setup embed and view.")
            await setup_channel.send(embed=embed, view=view)
            log.info(f"Setup message sent to {setup_channel.name} in {guild.name}")
        except Exception:
            log.exception(f"Failed to send setup message to {guild.name}")

    @app_commands.command(name="studio_setup", description="Set up or reconfigure the studio")
    @app_commands.default_permissions(manage_guild=True)
    async def studio_setup(self, interaction: discord.Interaction) -> None:
        """Manual studio setup command."""
        embed = discord.Embed(
            title="🛠️ Studio Setup",
            description=(
                "Let's configure the bot for your studio\n\n"
                "**Required Information:**\n"
                "🎓 Studio Number\n"
                "🔗 GitHub Repository\n\n"
            ),
            color=0x7289DA,
        )
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command can only be used in a server", ephemeral=True)
            return

        view = StudioSetupView(self._bot, guild)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="studio_info", description="View current studio configuration")
    async def studio_info(self, interaction: discord.Interaction) -> None:
        """View current studio configuration."""
        log.debug("Got 'studio_info' command")
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command can only be used in a server", ephemeral=True)
            return

        log.debug(f"I am in guild {guild.id} ")

        studio = await self._bot.get_studio(guild)
        log.debug(f"I have found studio - {studio} (could be nothing)")
        if not studio:
            embed = discord.Embed(
                title="❌ Studio Not Configured",
                description=("This server hasn't been set up yet.\n\nRun `/studio_setup` to configure your studio."),
                color=0xFF0000,
            )
        else:
            embed = discord.Embed(
                title=f"🎓 Studio {studio.studio_number} - {studio.studio_year} Bot",
                description=(
                    f"• Studio Number: {studio.studio_number}\n"
                    f"• Studio Year: {studio.studio_year}\n"
                    f"• GitHub Repo Name: {studio.repo_name}\n"
                    f"• Updated At: {studio.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                    f"• Created At: {studio.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                    "**Available Commands:**\n"
                    "• `/studio_setup` - Reconfigure studio (Admin Only)\n"
                    "• `/studio_info` - Get studio info\n"
                ),
                color=0x7289DA,
            )
            embed.set_footer(text=f"Studio ID: {studio.studio_number}")

        await interaction.response.send_message(embed=embed)
