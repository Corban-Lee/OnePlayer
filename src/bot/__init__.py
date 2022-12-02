""""""

import os
import time
import logging
import asyncio
from datetime import timedelta

import discord
from discord.ext import commands

from ._logs import setup_logs


log = logging.getLogger(__name__)


class Bot(commands.Bot):
    """This class is the root of the bot."""

    __slots__ = (
        "_start_time",
        "log_filepath",
        "cog_events",
        "all_cogs_loaded",
        "commands_synced",
        "debug"
    )

    def __init__(self, debug:bool=False):
        """Initialize the bot"""

        self.debug = debug

        # Roughly the time the bot was started
        self._start_time = time.time()

        super().__init__(
            command_prefix="ob ",
            intents=discord.Intents.all()
        )

        self.log_filepath = setup_logs()
        self.commands_synced = False

        # Event that can be used to await for all cogs to be loaded
        self.all_cogs_loaded = asyncio.Event()
        self.cog_events = {}
 
    async def _determine_loaded_cogs(self):
        """Determine which cogs are loaded"""

        log.info("Determining loaded cogs")

        await asyncio.gather(
            *[event.wait() for event in self.cog_events.values()]
        )
        await self.wait_until_ready()
        self.all_cogs_loaded.set()

    @property
    def uptime(self) -> timedelta:
        """Returns the bot's uptime as a timedelta object"""

        difference = int(round(time.time() - self._start_time))
        return timedelta(seconds=difference)

    @property
    def start_time(self) -> str:
        """Returns the bot's start time as a string object"""

        _time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self._start_time))
        return f'{_time}'

    async def sync_app_commands(self) -> None:
        """Sync app commands with discord"""

        log.info('Syncing App Commands')

        # Syncing requires a ready bot
        await self.wait_until_ready()

        if not self.commands_synced:
            await self.tree.sync()
            self.commands_synced = True
            log.info('App Commands Synced')

    async def on_ready(self) -> None:
        """Handles tasks that require the bot to be ready first.

        This is called when the bot is ready by discord.py
        """

        log.info("Bot has logged-in and is ready!")
        log.debug(
            f"Name: %s - ID: %s",
            self.user.name,
            self.user.id
        )


        self.loop.create_task(self._determine_loaded_cogs())

        # Sync app commands with discord
        await self.sync_app_commands()

        log.info("Bot startup tasks complete")

    async def close(self):
        """Takes care of some final tasks before closing the bot

        This is called when the bot is closed by discord.py
        """

        log.info("I am now shutting down")

    async def load_extensions(self):
        """Searches through the ./ext/ directory and loads them"""

        log.info('Loading extensions')

        for filename in os.listdir('./src/ext'):

            # Skip non cog files
            if not filename.endswith('.py') or filename.startswith('_'):
                log.info(
                    "File \"%s\" is not an extension, skipping",
                    filename
                )
                continue

            # Load the extension file
            await self.load_extension(f'ext.{filename[:-3]}')
            log.info('Loading: %s', filename)
