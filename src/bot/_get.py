"""Module for retrieving objects using the cache or the discord API."""

import logging
import discord
from discord.ext.commands import Bot


log = logging.getLogger(__name__)


class Get:
    """Class for retrieving objects using the cache or the discord API."""

    def __init__(self, bot:Bot):
        self.bot = bot

    async def guild(self, _id:int, /) -> discord.Guild | None:
        """Get a discord guild object from an ID.

        Args:
            id (int): The ID of the guild.
        Returns:
            discord.Guild: The guild object.
            None: If the guild is not found.
        """

        log.debug('Getting guild object')
        guild_obj = self.bot.get_guild(_id)
        return guild_obj or await self.bot.fetch_guild(_id)

    async def role(self, role_id, guild_id, /) -> discord.Role | None:
        """Get a discord Role object from an ID.

        Args:
            id (int): The ID of the role.
        Returns:
            discord.Role: The role object.
            None: If the role is not found.
        """

        log.debug('Getting role object')
        guild_obj = await self.guild(guild_id)
        role_obj = guild_obj.get_role(role_id)
        return role_obj

    async def channel(self, _id:int, /) -> discord.TextChannel | None:
        """Get a discord channel object from an ID.

        Args:
            id (int): The ID of the channel.
        Returns:
            discord.TextChannel: The channel object.
            None: If the channel is not found.
        """

        log.debug('Getting channel object')
        channel_obj = self.bot.get_channel(_id)
        return channel_obj or await self.bot.fetch_channel(_id)

    async def user(self, _id, /) -> discord.User | None:
        """Get a discord member object from an ID.

        Args:
            id (int): The ID of the member.
        Returns:
            discord.Member: The member object.
            None: If the member is not found.
        """

        log.debug('Getting user object')
        member_obj = self.bot.get_user(_id)
        return member_obj or await self.bot.fetch_user(_id)

    async def member(self, member_id, guild_id, /) -> discord.Member:
        """Get a discord Member from a Guild"""

        log.debug('Getting member object')
        guild_obj = await self.guild(guild_id)
        member_obj = guild_obj.get_member(member_id)
        return member_obj or await guild_obj.fetch_member(member_id)
