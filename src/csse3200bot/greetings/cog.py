"""Greetings Cog Module."""

import discord
from discord import app_commands
from discord.ext import commands

from csse3200bot.bot import CSSEBot


class GreetingsCog(commands.GroupCog, name="say"):
    """Greetings cog."""

    _bot: CSSEBot

    def __init__(self, bot: CSSEBot) -> None:
        """Constructor."""
        self._bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Listener for when a member joins."""
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f"Welcome {member.mention}.")

    @app_commands.command(name="hello")
    @app_commands.describe(thing_to_say="This is the thing to say")
    async def better_hello(self, interaction: discord.Interaction, thing_to_say: str) -> None:
        """Better hello command."""
        await interaction.response.send_message(f"{thing_to_say} - BOOM, said a thing")
