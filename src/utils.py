"""Utils for the bot."""

import logging

from discord import app_commands, Interaction as Inter


log = logging.getLogger(__name__)


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
