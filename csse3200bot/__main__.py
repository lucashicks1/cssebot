"""Main module."""

import asyncio
import logging


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    # _ = discord.Intents.default()
    # # Not sure what intents we need atm

    print("STARTING UP")


asyncio.run(main())
