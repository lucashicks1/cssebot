"""Main module."""

import logging

import discord

from csse3200bot.bot import DiscordBot
from csse3200bot.config import CONFIG

logging.basicConfig(level=logging.INFO)

"""
Setup bot intents (events restrictions)
For more information about intents, please go to the following websites:
https://discordpy.readthedocs.io/en/latest/intents.html
https://discordpy.readthedocs.io/en/latest/intents.html#privileged-intents


Default Intents:
intents.bans = True
intents.dm_messages = True
intents.dm_reactions = True
intents.dm_typing = True
intents.emojis = True
intents.emojis_and_stickers = True
intents.guild_messages = True
intents.guild_reactions = True
intents.guild_scheduled_events = True
intents.guild_typing = True
intents.guilds = True
intents.integrations = True
intents.invites = True
intents.messages = True # `message_content` is required to get the content of the messages
intents.reactions = True
intents.typing = True
intents.voice_states = True
intents.webhooks = True

Privileged Intents (Needs to be enabled on developer portal of Discord), please use them only if you need them:
intents.members = True
intents.message_content = True
intents.presences = True
"""
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

logger = logging.getLogger("csse3200bot")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("discord-bots.log", encoding="utf-8", mode="w")

logger.addHandler(console_handler)
logger.addHandler(file_handler)

bot = DiscordBot(command_prefix="!", intents=intents)

bot.run(CONFIG.discord_bot_token, log_handler=None)
