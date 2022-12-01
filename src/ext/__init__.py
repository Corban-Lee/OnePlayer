"""Contains base cog for all cogs to inherit from."""

import logging
import asyncio

from discord.ext import commands


log = logging.getLogger(__name__)


class BaseCog(commands.Cog):
    """A cog class that all cogs should inherit from."""

    def __init__(self, bot):
        super().__init__()
        self.bot: commands.Bot = bot

    @commands.Cog.listener(name="on_ready")
    async def _on_ready(self):
        """
        Method called when the cog has been loaded.
        Logs a ready message.
        """

        # Add the cog to the bot's list of cogs
        event = self.bot.cog_events[self.qualified_name] = asyncio.Event()
        event.set()
        

        log.info(f"Cog loaded: {self.qualified_name}")
