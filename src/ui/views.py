"""Views for the bot"""

import logging

import discord
from discord import (
    Interaction as Inter,
    ui as dui,
    ButtonStyle
)


log = logging.getLogger(__name__)


class TrackAddedView(dui.View):
    """View for the track added message, has controls for managing the 
    added track in the queue"""

    __slots__ = ("song", "voice_state")

    def __init__(self, song, voice_state):
        super().__init__(timeout=300)
        self.song = song
        self.voice_state = voice_state

    @dui.button(
        label="Play Now",
        style=ButtonStyle.primary
    )
    async def play_now(self, inter:Inter, button:dui.Button):
        """Skip the queue and play the added track now"""

        # Lock this command to users with elevated permissions
        permissions = inter.channel.permissions_for(inter.user)
        if discord.Permissions(moderate_members=True) not in permissions:
            return await inter.response.send_message(
                "You don't have permission to do that",
                ephemeral=True
            )

        # Ensure that the song is not already playing
        if self.voice_state.current == self.song:
            return await inter.response.send_message(
                "This song is already playing",
                ephemeral=True
            )        

        await inter.response.send_message(
            "Skipping queue and playing now..."
        )

        # Skip the queue and play the song now
        self.voice_state.skip_to_song(
            self.voice_state.queue.index(self.song)
        )


    @dui.button(
        label="Remove from Queue",
        style=ButtonStyle.secondary
    )
    async def remove_from_queue(self, inter:Inter, button:dui.Button):
        await inter.response.send_message("dummy")
        if inter.user != self.voice_state.current.requester:
            return await inter.response.send_message(
                "You are not the requester of this song",
                ephemeral=True
            )


class MusicControlView(dui.View):
    """View for music control buttons"""

    __slots__ = ("song_id",)

    # TODO: layout 3 rows
    # 1st row: backward, resume/pause, forward
    # 2nd row: mute/unmute, volume down, volume up
    # 3rd row: loop, stop, shuffle

    def __init__(self, voice_state):
        super().__init__(timeout=300)
        self.voice_state = voice_state
        self.song = voice_state.current

    def ensure_current_song(self):
        """Ensures that the current song is the same as the one that the 
        view was created with"""
        if self.song != self.voice_state.current:
            raise ValueError(
                "The current song has changed, please use the new "
                "controls for that song"
            )

    @dui.button(
        emoji="⏮️",
        style=ButtonStyle.secondary,
        row=0
    )
    async def rewind(self, inter:Inter, button:dui.Button):
        self.ensure_current_song()
        await inter.response.send_message("dummy")

    @dui.button(
        emoji="⏯️",
        style=ButtonStyle.secondary,
        row=0
    )
    async def pause_resume(self, inter:Inter, button:dui.Button):
        self.ensure_current_song()
        await inter.response.send_message("dummy")

    @dui.button(
        emoji="⏭️",
        style=ButtonStyle.secondary,
        row=0
    )
    async def forward(self, inter:Inter, button:dui.Button):
        self.ensure_current_song()
        await inter.response.send_message("dummy")

    @dui.button(
        emoji="🔇",
        style=ButtonStyle.secondary,
        row=1
    )
    async def mute(self, inter:Inter, button:dui.Button):
        self.ensure_current_song()
        await inter.response.send_message("dummy")

    @dui.button(
        emoji="🔉",
        style=ButtonStyle.secondary,
        row=1
    )
    async def volume_down(self, inter:Inter, button:dui.Button):
        self.ensure_current_song()
        await inter.response.send_message("dummy")

    @dui.button(
        emoji="🔊",
        style=ButtonStyle.secondary,
        row=1
    )
    async def volume_up(self, inter:Inter, button:dui.Button):
        self.ensure_current_song()
        await inter.response.send_message("dummy")

    @dui.button(
        emoji="🔁",
        style=ButtonStyle.secondary,
        row=2
    )
    async def loop(self, inter:Inter, button:dui.Button):
        self.ensure_current_song()
        await inter.response.send_message("dummy")

    @dui.button(
        emoji="⏹️",
        style=ButtonStyle.secondary,
        row=2
    )
    async def stop(self, inter:Inter, button:dui.Button):
        self.ensure_current_song()
        await inter.response.send_message("dummy")

    @dui.button(
        emoji="🔀",
        style=ButtonStyle.secondary,
        row=2
    )
    async def shuffle(self, inter:Inter, button:dui.Button):
        self.ensure_current_song()
        await inter.response.send_message("dummy")
