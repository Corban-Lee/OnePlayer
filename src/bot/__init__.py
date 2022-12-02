""""""

import os
import time
import logging
import asyncio
from sqlite3 import IntegrityError
from datetime import timedelta

import discord
from discord.ext import commands, tasks

from db import db
from db.enums import ChannelPurposes
from ui import ManageTicketView
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
 
    @tasks.loop(minutes=10)
    async def _autosave_db(self):
        """Autosave the database"""

        log.info("Autosaving database")
        db.commit()

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

    async def sync_guilds(self) -> None:
        """Sync guilds with the database"""

        log.info("Syncing guilds with the database")

        await self.wait_until_ready()

        for guild in self.guilds:
            try:
                log.debug("Syncing guild %s", guild.name)
                db.execute(
                    "INSERT INTO guilds (guild_id) VALUES (?)",
                    guild.id
                )
            except IntegrityError as err:
                log.debug(
                    "Guild %s already exists in the database",
                    guild.name
                )
                continue

    async def send_logs(self, msg:str, include_file:bool=False) -> None:
        """Send a message to all purposed log channels

        Args:
            msg (str): The message to send.
            include_file (bool, optional): Whether to include the log file. Defaults to False.
        """

        log.info("Sending logs to all logging channels")

        log_channel_ids = db.column(
            "SELECT object_id FROM purposed_objects WHERE purpose_id = " 
            "(SELECT id FROM purposes WHERE name = ?)",
            ChannelPurposes.botlogs.value
        )

        log.debug(
            "Found %s logging channels, sending",
            len(log_channel_ids)
        )

        for channel_id in log_channel_ids:

            # Get the channel and send the message
            channel = await self.get.channel(channel_id)
            await channel.send(msg)

            # Follow up with a new log file if requested
            if include_file:
                filename = os.path.basename(self.log_filepath)
                file = discord.File(self.log_filepath, filename=filename)
                await channel.send(file=file)

    async def on_guild_join(self, guild:discord.Guild):
        """Sync the guilds when the bot joins a new guild"""

        log.info('Joined guild %s', guild.name)
        await self.sync_guilds()

    async def on_guild_remove(self, guild:discord.Guild):
        """Called when the bot leaves a guild"""

        log.info('Left guild %s', guild.name)

        # db.execute(
        #     "DELETE FROM guilds WHERE guild_id = ?",
        #     guild.id
        # )

        # log.info("Removed guild %s from the database", guild.name)

    async def setup_hook(self) -> None:

        active_ticket_ids = db.column(
            "Select id FROM tickets WHERE active = ?",
            1
        )

        for ticket_id in active_ticket_ids:
            self.add_view(ManageTicketView(ticket_id))

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

        await self.send_logs('**I\'m back online!**')

        # Schedule bot tasks
        self._autosave_db.start()
        self.loop.create_task(self._determine_loaded_cogs())

        # Sync the guilds with the db and the app commands with discord
        await self.sync_guilds()
        await self.sync_app_commands()

        log.info("Bot startup tasks complete")

    async def close(self):
        """Takes care of some final tasks before closing the bot

        This is called when the bot is closed by discord.py
        """

        log.info("I am now shutting down")

        # IMPORTANT: without this commit all changes will be lost
        db.commit()
        log.debug("Final database commit complete")

        filename = os.path.basename(self.log_filepath)

        # Send a ready message to all logging channels
        await self.send_logs(
            'I\'m shutting down, here are the logs for this session.' \
            f'\nStarted: {filename[:-4]}\nUptime: {str(self.uptime)}',
            include_file=True
        )
        await super().close()

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
