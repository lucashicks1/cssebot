import asyncio
import logging


async def main():
    logging.basicConfig(level=logging.INFO)
    print("HELLO")


asyncio.run(main())
