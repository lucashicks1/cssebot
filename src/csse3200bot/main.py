"""Main module."""

import logging

import discord

from csse3200bot.config import CONFIG

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
# # Not sure what intents we need atm
client = discord.Client(intents=intents)

client.run(CONFIG.discord_bot_token)
