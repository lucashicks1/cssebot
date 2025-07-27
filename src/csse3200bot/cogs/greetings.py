"""Greetings Cog Module."""

import discord
from discord import app_commands
from discord.ext import commands


class GreetingsCog(commands.Cog):
    """Greetings cog."""

    def __init__(self) -> None:
        """Constructor."""

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Listener for when a member joins."""
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f"Welcome {member.mention}.")

    @commands.command()
    async def hello(self, ctx: commands.Context, *, member: discord.User | discord.Member | None = None) -> None:
        """Says hello."""
        member = member or ctx.author

        await ctx.send(f"Hello {member.name}... This feels familiar.")

    @app_commands.command()
    @app_commands.describe(thing_to_say="This is the thing to say")
    async def better_hello(self, interaction: discord.Interaction, thing_to_say: str) -> None:
        """Better hello command."""
        await interaction.response.send_message(f"{thing_to_say} - BOOM, said a thing")
