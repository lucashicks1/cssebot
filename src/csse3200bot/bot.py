"""Bot Module."""

from typing import Any

from discord.ext import commands

from csse3200bot.cogs.greetings import GreetingsCog


class DiscordBot(commands.Bot):
    """Custom csse bot."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401, D107
        super().__init__(*args, **kwargs)

    # https://discordpy.readthedocs.io/en/stable/api.html#discord.Client.setup_hook
    # This is called when the bot starts
    async def setup_hook(self) -> None:
        """Setup."""
        # Setup the cogs -> I'm not a huge fan of registering them by name because things can get missed
        await self.add_cog(GreetingsCog())

        # Setup some internal state
        # Maybe the discord servers
        await self.tree.sync()
