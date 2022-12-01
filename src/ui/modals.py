"""ui modals"""

import logging
from typing import Callable, Coroutine
from datetime import datetime
import discord
from discord import Interaction as Inter
from discord import ui as dui


log = logging.getLogger(__name__)


class TicketModal(dui.Modal):
    """Create a new ticket"""

    description = dui.TextInput(
        label="What can we help you with?",
        style=discord.TextStyle.long,
        required=True,
        placeholder="Please describe your issue"
    )

    def __init__(self, title:str, callback):
        super().__init__(title=title)
        self.callback = callback

    async def on_submit(self, inter:Inter):  # pylint: disable=arguments-differ
        """Called when the modal is submitted"""

        # Provide the callback with the ticket description
        # and an interaction to respond to
        await self.callback(
            inter=inter,
            description=self.description.value
        )


class MakeEmbedModal(dui.Modal, title="Create Embed"):
    """Create a custom embed"""

    title_input = dui.TextInput(
        label="Embed Title",
        placeholder="My really cool embed",
        style=discord.TextStyle.short,
        required=True,
        min_length=1,
        max_length=256
    )
    description_input = dui.TextInput(
        label="Embed Description",
        placeholder="This descibes my awesome embed",
        style=discord.TextStyle.long,
        required=True,
        min_length=1,
        max_length=2048
    )
    colour_input = dui.TextInput(
        label="Embed Colour [Hex Format]",
        placeholder="#FFFFFF",
        default="#FFFFFF",
        style=discord.TextStyle.short,
        required=False,
        min_length=7,
        max_length=7
    )

    def __init__(self, coro: Coroutine):
        super().__init__()
        self.coro = coro

    async def on_submit(self, inter:Inter): # pylint: disable=arguments-differ
        await self.coro(
            _inter=inter,
            title=self.title_input.value,
            description=self.description_input.value,
            colour=self.colour_input.value
        )


class BanMemberModal(dui.Modal, title="Confirm Ban"):
    """Confirm a ban before proceeding"""

    reason_input = dui.TextInput(
        label="Reason For Ban:",
        placeholder="Example: violating the rules, spamming, etc.",
        style=discord.TextStyle.long,
        required=False
    )

    def __init__(self, member:discord.Member):
        super().__init__()
        self.member = member

        log.debug("Initialized %s", self.__class__.__name__)

    async def on_submit(self, inter:Inter): # pylint: disable=arguments-differ

        log.debug("Banning %s", self.member)

        try:
            await self.member.ban(reason=self.reason_input.value)
        except discord.Forbidden as err:
            log.error(err)
            await inter.response.send_message(
                "I do not have permission to ban this member, "
                "consider updating my permissions and try again.",
            )
            return

        log.info("Banned %s from %s", self.member, self.member.guild.name)
        await inter.response.send_message(
            f"Successfully banned {self.member} "
            f"for {self.reason_input.value}"
        )


class BirthdayModal(dui.Modal, title='Birthday'):
    """Modal for submitting member birthdays"""

    birthday_input = dui.TextInput(
        label='Please enter your birthday!',
        placeholder='DD/MM/YYYY',
        style=discord.TextStyle.short
    )

    def __init__(self, save_func:Callable):
        super().__init__()
        self._save_func = save_func

    async def on_submit(self, inter:Inter):  # pylint: disable=arguments-differ

        # Get the entered birthday
        value = self.birthday_input.value
        bday = datetime.strptime(value, "%d/%m/%Y")

        # Get the validation range
        now = datetime.now()
        valid_range = range(now.year-40, now.year-12)

        # Check that the birthday date range is valid
        if bday.year not in valid_range:
            raise OverflowError()

        self._save_func(value)

        await inter.response.send_message(
            'I\'ve saved your special date, '
            'I can\'t wait to wish you a happy birthday!',
            ephemeral=True
        )

    async def on_error(self, inter:Inter, error):  # pylint: disable=arguments-differ

        if isinstance(error, ValueError):
            msg = 'Invalid date format. Please try again.'

        elif isinstance(error, OverflowError):
            msg = 'Date is too far into the past or present.' \
                'Please try again.'

        else:
            msg = f'An unknown issue occured. Contact an admin.' \
                f'\nError: {error}'

        await inter.response.send_message(
            content=msg,
            ephemeral=True
        )
