"""Utils for the bot."""

import os
import logging
from math import floor, log as mlog

import discord
from discord import app_commands, Interaction as Inter


log = logging.getLogger(__name__)

async def get_member(interaction: discord.Interaction, member: str):
    """Convert a username or user id into a discord.Member
    object and return it.

    Args: TODO

    Returns: TODO
    """

    guild = interaction.guild

    # If the member is digits, it's likely a user id
    if member.isdigit():
        return guild.get_member(int(member))

    # Otherwise, it's likely a username, so we'll use that
    return guild.get_member_named(member)

def list_cogs() -> list[str]:
    """Returns a list of strings containing the filenames of all cogs.

    Returns:
        list[str]: List of cog filenames.
    """
    return [
        filename for filename in os.listdir('./src/ext')
        if filename.endswith('.py') and not filename.startswith('__')
    ]

def to_choices(string_list:list[str]) -> list[app_commands.Choice[str]]:
    """Converts a list of strings to a list of Choice objects.

    Returns:
        list[app_commands.Choice[str]]: The list of choices.
    """
    return [
        app_commands.Choice(name=i, value=i)
        for i in string_list
    ]

async def is_bot_owner(inter:Inter):
    """Checks if the user is the owner of the bot"""

    return await inter.client.is_owner(inter.user)

def is_admin(inter:Inter, bot) -> bool:
    """Returns bool if member has admin role"""

    role = discord.utils.get(inter.guild.roles, id=bot.config['guild']['role_ids']['admin'])
    return role in inter.user.roles

def normalized_name(member:discord.Member, with_id:bool=True) -> str:
    """Returns the member's name followed by their
    discriminator and ID.

    Args:
        member (discord.Member): The member to get the name of.
        with_id (bool, optional): Whether to include the ID. Defaults to True.
    """

    output = f'{member.name}#{member.discriminator}'
    return output if not with_id else f'{output} ({member.id})'

def abbreviate_num(num:float) -> str:
    """Abbreviates a number to a string with the appropriate suffix

    Args:
        num (float): The number to abbreviate.

    Returns:
        str: The abbreviated number.
    """

    if num < 1000:
        return str(floor(num))

    out = int(floor(mlog(num, 1000)))
    suffix = 'KMBT'[out - 1]
    return f'{num / 1000 ** out:.2f}{suffix}'
