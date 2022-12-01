"""Entry point for the bot, run this file to get things started."""

import asyncio
import argparse

from bot import Bot

# Parse command line arguments
parser = argparse.ArgumentParser(
    prog="OnePlayer",
    description="A Discord bot for the OneBot project."
)
parser.add_argument(
    "-t", "--token",
    help="The bot token to use for authentication.",
    required=False,
    type=str
)
parser.add_argument(
    "-d", "--debug",
    help="Run the bot in debug mode.",
    required=False,
    action="store_true"
)

async def main():
    """Main function for starting the application"""

    args = parser.parse_args()

    if args.token is None:
        # NOTE: You will need to create this file if it
        # doesn't exist and paste your bot token in it.
        with open('TOKEN', 'r', encoding='utf-8') as file:
            token = file.read()
    else:
        token = args.token

    # Construct the bot, load the extensions and start it up!
    async with Bot(debug=args.debug) as bot:
        await bot.load_extensions()
        await bot.start(token, reconnect=True)


if __name__ == '__main__':
    asyncio.run(main())
