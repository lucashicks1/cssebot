"""Studio Utils."""

import functools
import logging
from typing import Any

import discord

from csse3200bot.bot import CSSEBot

log = logging.getLogger(__name__)


def studio_required(func):
    """Decorator that checks if a guild has been setup with a studio before executing the command.

    This should be applied to app_commands that require a studio to be set up.
    If no studio is found, it will send an error message to the person who sent the command.

    Usage (Only good bit of docs I've done):
        @app_commands.command(name="example")
        @studio_required()
        async def some_command(self, interaction: discord.Interaction) -> None:
            # Command implementation here
            ...
    """

    @functools.wraps(func)
    async def wrapper(self: Any, interaction: discord.Interaction, *args, **kwargs) -> Any:
        guild = interaction.guild

        if guild is None:
            log.warning(f"Command {func.__name__} used outside of guild")
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return None

        if hasattr(self, "_bot"):  # python magic
            bot: CSSEBot = self._bot
        elif isinstance(self, CSSEBot):
            bot = self
        else:
            log.error(f"Could not find the bot instance in {func.__name__}")
            await interaction.response.send_message(
                "Bot configuration error, Lucas has something wrong here", ephemeral=True
            )
            return None

        # studio_exists
        studio = await bot.get_studio(guild)
        if studio is None:
            msg = "This command requires a studio to be set up for the guild - staff use `/studio setup` for this."

            await interaction.response.send_message(
                msg,
                ephemeral=True,
            )
            return None

        # Studio exists, proceed with the original command
        return await func(self, interaction, *args, **kwargs)

    return wrapper
