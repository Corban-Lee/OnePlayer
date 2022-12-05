"""Extension for music commands"""

import asyncio
import logging
import functools
import itertools
import random
import math
from async_timeout import timeout
from enum import Enum, auto
from abc import ABC, abstractmethod

import discord
from discord import (
    app_commands,
    Interaction as Inter,
    VoiceClient
)
import youtube_dl

from ui import (
    AddedTrackEmbed,
    TrackAddedView,
    NowPlayingEmbed,
    MusicQueueEmbed
)
from exceptions import VoiceError, YTDLError
from constants import (
    MUSIC_CANTLEAVEVC,
    MUSIC_USERNOTINVC,
    MUSIC_NOTPLAYING,
    MUSIC_QUEUEEMPTY,
    MUSIC_BOTDIFFVC,
    MUSIC_JOINEDVC,
    MUSIC_LEFTVC,
    MUSIC_SKIPPEDSONG,
    MUSIC_SKIPVOTEREGISTERED,
    MUSIC_ALREADYVOTEDTOSKIP,
    MUSIC_RESUMED,
    MUSIC_PAUSED,
    MUSIC_STOPPED,
    MUSIC_LOOPING,
    MUSIC_NOTLOOPING,
    MUSIC_ADDEDPLAYSOON,
    INVALID_PAGE_NUMBER
)
from . import BaseCog


# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ''

log = logging.getLogger(__name__)


class Sources(Enum):
    Youtube = auto()  # not following name convensions here because the
    Spotify = auto()  # variable names are show on the user interface


class Source(ABC):
    """Represents a source for audio content"""

    requester: discord.User
    channel: discord.TextChannel
    data: dict

    uploader: str
    uploader_url: str
    upload_date: str
    thumbnail: str
    title: str
    description: str

    @classmethod
    @abstractmethod
    async def from_query(cls, *args, **kwargs):
        pass


class YTDLSource(Source, discord.PCMVolumeTransformer):
    """Represents a youtube source for audio content"""

    __slots__ = ()

    YTDL_OPTIONS = {"default_search": "auto"}
    FFMPEG_OPTIONS = {"options": "-vn"}
    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, inter: Inter, ffmpeg_source: discord.FFmpegPCMAudio, *, data: dict, volume:float=0.5):
        super().__init__(ffmpeg_source, volume)

        self.requester: discord.User = inter.user
        self.channel: discord.TextChannel = inter.channel
        self.data = data

        log.debug(data)

        # shorthands for audio data
        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        self.upload_date = data.get('upload_date')
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = int(data.get('duration'))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')


    @classmethod
    async def from_query(cls, inter:Inter, query:str, async_loop:asyncio.BaseEventLoop):
        """Create a youtube source from a search query"""

        log.debug("from youtube query")

        data = await async_loop.run_in_executor(None, lambda: cls.ytdl.extract_info(query, download=False))

        if "entries" in data:
            data = data["entries"][0]

        filename = cls.ytdl.prepare_filename(data)
        return cls(inter, discord.FFmpegPCMAudio(filename, **cls.FFMPEG_OPTIONS, executable="bin/ffmpeg.exe"), data=data)


class SpotifySource(Source, discord.PCMVolumeTransformer):
    """Represents a spotiy source for audio content"""

    @classmethod
    async def from_query(cls, inter:Inter, search:str, async_loop:asyncio.BaseEventLoop):
        """Create a spotify source from a search query"""
        pass


class Song:
    """A class to represent a song"""

    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):

        log.debug("Creating Song instance")

        self.source = source
        self.requester = source.requester


class SongQueue(asyncio.Queue):
    """Queue that holds songs"""

    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(
                self._queue,
                item.start,
                item.stop,
                item.step
            ))

        return self._queue[item]

    def __iter__(self):  # pylint: disable=non-iterator-returned
        return self._queue.__iter__()

    def __len__(self) -> int:
        return self.qsize()

    def index(self, song:Song) -> int:
        """Returns the index of a song in the queue"""

        return self._queue.index(song)

    def __contains__(self, song:Song) -> bool:
        return song in self._queue

    def rotate(self, index: int) -> None:
        """Rotates a song to the top of the queue"""

        self._queue.rotate(index)

    def clear(self) -> None:
        """Clears the queue"""

        self._queue.clear()

    def shuffle(self) -> None:
        """Shuffles the queue"""

        random.shuffle(self._queue)

    def remove(self, index: int) -> None:
        """Removes a song from the queue"""

        del self._queue[index]


class VoiceState:
    """A class to control the voice client, a new instance is created
    for each guild where the bot is present in a voice channel"""

    __slots__ = (
        "bot",
        "inter",
        "current",
        "voice",
        "next",
        "queue",
        "_loop",
        "_volume",
        "skip_votes",
        "audio_player"
    )

    def __init__(self, bot, inter:Inter):

        log.debug("Creating VoiceState instance")

        self.bot = bot
        self.inter = inter

        self.current: Song = None
        self.voice: VoiceClient = None
        self.next = asyncio.Event()
        self.queue = SongQueue()

        self._loop = False
        self._volume = 0.5  # min: 0.01, max: 1.00
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self) -> None:
        self.audio_player.cancel()

    @property
    def loop(self) -> bool:
        """Returns the loop status"""

        return self._loop

    @loop.setter
    def loop(self, value: bool) -> None:
        """Sets the loop status"""

        self._loop = value

    @property
    def volume(self) -> float:
        """Returns the volume"""

        return self._volume

    @volume.setter
    async def volume(self, value: float) -> None:
        """Sets the volume"""

        self._volume = value

    @property
    def is_playing(self) -> bool:
        """Returns True if the voice client is playing"""

        return self.voice and self.current

    async def audio_player_task(self) -> None:
        """Background task that handles the audio player"""

        log.debug("Starting audio player task")

        while True:
            self.next.clear()

            if not self.loop:
                self.current = None
                try:

                    # Get the next song or timeout in 3 minutes
                    async with timeout(180):
                        log.debug("fetching song from queue")
                        self.current = await self.queue.get()

                except asyncio.TimeoutError:
                    log.debug("TimeoutError: no song in queue")
                    self.bot.loop.create_task(self.stop())
                    return

            log.debug("Playing song %s", self.current.source.title)

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(
                embed=NowPlayingEmbed(self.current),
                # view=MusicControlView(self)
            )
            await self.next.wait()

    def play_next_song(self, error=None):
        """Plays the next song in the queue"""

        log.debug("Playing next song")

        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip_to_song(self, index: int):
        """Skips to a song in the queue"""

        log.debug("Skipping to song %s", index)

        if not 0 <= index < len(self.queue):
            raise VoiceError(f"Song #{index} does not exist.")

        self.queue.rotate(-index)
        self.skip()

    def skip(self):
        """Skips the current song"""

        log.debug("Skipping song")

        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        """Stops the player and clears the queue"""

        self.queue.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class MusicCog(BaseCog, name="New Music"):
    """Cog for music commands"""

    __slots__ = ()
    voice_states = {}

    async def cog_unload(self) -> None:
        """Cleanup when cog is unloaded"""

        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def get_voice_state(self, inter:Inter, /):
        """Get the voice state of the guild"""

        try:
            return self.voice_states[inter.guild.id]
        except KeyError:
            state = VoiceState(self.bot, inter)
            self.voice_states[inter.guild.id] = state
            return state

    @staticmethod
    async def check_member_in_vc(inter:Inter) -> bool:
        """Check if the member is in a voice channel, also checks
        if the bot is already in another voice channel.

        Returns:
            bool: True if the member is in a voice channel
        raises:
            app_commands.CheckFailure: If the member is not in a
                voice channel
        """

        if not inter.user.voice or not inter.user.voice.channel:
            raise app_commands.CheckFailure(MUSIC_USERNOTINVC)

        if inter.guild.voice_client:
            if inter.guild.voice_client.channel != inter.user.voice.channel:
                raise app_commands.CheckFailure(MUSIC_BOTDIFFVC)

        return True

    async def check_is_playing(self, inter:Inter) -> bool:
        """Check if the bot is currently playing a song

        Returns:
            bool: True if the bot is playing a song
        Raises:
            app_commands.CheckFailure: If the bot is not playing a song
        """

        if not self.get_voice_state(inter).check_playing:
            raise app_commands.CheckFailure(MUSIC_NOTPLAYING)

        return True


    async def join_vc(self, inter: Inter) -> None:
        """Join the voice channel of the user who invoked the command"""

        voice_channel = inter.user.voice.channel
        voice_state = self.get_voice_state(inter)

        if inter.guild.voice_client:
            await inter.guild.voice_client.move_to(voice_channel)
            return

        voice_state.voice: VoiceClient = await voice_channel.connect()

    @app_commands.command(name="join")
    @app_commands.check(check_member_in_vc)
    async def join_vc_cmd(self, inter:Inter):
        """Joins the current voice channel"""

        await self.join_vc(inter)
        await inter.response.send_message(MUSIC_JOINEDVC)

    @app_commands.command(name="leave")
    @app_commands.default_permissions(move_members=True)
    @app_commands.check(check_member_in_vc)
    async def leave_vc_cmd(self, inter:Inter):
        """Leaves the current voice channel"""

        if not inter.guild.voice_client:
            await inter.response.send_message(MUSIC_CANTLEAVEVC)
            return

        voice_state = self.get_voice_state(inter)
        await voice_state.stop()
        del self.voice_states[inter.guild.id]
    
        await inter.response.send_message(MUSIC_LEFTVC)

    @app_commands.command(name="currently-playing")
    @app_commands.check(check_member_in_vc)
    async def currently_playing_cmd(self, inter:Inter):
        """Shows the currently playing song"""

        voice_state = self.get_voice_state(inter)

        if not voice_state.is_playing:
            await inter.response.send_message(MUSIC_NOTPLAYING)
            return

        # Send an embed for the currently playing song
        await inter.response.send_message(
            embed=NowPlayingEmbed(voice_state.current),
            # view=MusicControlView(voice_state)
        )

    @app_commands.command(name="queue")
    @app_commands.check(check_member_in_vc)
    async def queue_cmd(self, inter:Inter, page:int=1):
        """Shows the music player's queue. There are 10 tracks shown
        per page.

        Args:
            page (int, optional): The page to show. Defaults to 1.
        """

        log.debug("Checking the queue for page %s", page)

        voice_state = self.get_voice_state(inter)

        # Check if the queue is empty first
        if len(voice_state.queue) == 0:
            await inter.response.send_message(MUSIC_QUEUEEMPTY)
            return

        # Determine the amount of pages
        items_per_page = 10
        pages = math.ceil(len(voice_state.queue) / items_per_page)

        # Check that the input page number is valid
        if page not in range(1, pages + 1):
            return await inter.response.send_message(
                INVALID_PAGE_NUMBER.format(pages)
            )

        # Get the items index range for the page
        start = (page - 1) * items_per_page
        end = start + items_per_page

        # Create an output string containing the page info
        output = f"**Music Queue - {len(voice_state.queue)} tracks**\n\n"
        for i, song in enumerate(voice_state.queue[start:end], start=start):
            output += f"{i+1}. [{song.source.title}]({song.source.url})\n"

        log.debug("Finished creating queue output")

        embed = MusicQueueEmbed(
            description=output,
            current_page=page,
            total_pages=pages
        )
        await inter.response.send_message(embed=embed)

    @app_commands.command(name="skip")
    @app_commands.check(check_member_in_vc)
    async def skip_cmd(self, inter:Inter):
        """Skips the currently playing song. Requires 3 votes unless
        the requester or an admin skips the song."""

        voice_state = self.get_voice_state(inter)

        log.debug("Checking if the user can skip the song")

        # Check that there is a song playing
        if not voice_state.is_playing:
            log.debug("No song is playing")
            await inter.response.send_message(MUSIC_NOTPLAYING)
            return

        # Allow the requester or admins to skip the song
        if inter.user == voice_state.current.requester or \
            inter.user.guild_permissions.administrator:
            await inter.response.send_message(MUSIC_SKIPPEDSONG)
            voice_state.skip()

            log.debug(
                "The user is the requester or an admin, "
                "so I've skipped the song"
            )

        # Allow the user to vote to skip if they haven't already
        elif inter.user.id not in voice_state.skip_votes:
            voice_state.skip_votes.add(inter.user.id)
            total_votes = len(voice_state.skip_votes)

            log.debug("The user has voted to skip the song")

            # We can skip the song if we have 3 votes
            if total_votes >= 3:
                await inter.response.send_message(MUSIC_SKIPPEDSONG)
                voice_state.skip()

                log.debug("3 votes reached. The song has been skipped")

            # Not enough votes, tell the user how many more are needed
            else:
                await inter.response.send_message(
                    MUSIC_SKIPVOTEREGISTERED.format(3-total_votes)
                )

        # The only other option is that the user has already voted
        else:
            await inter.response.send_message(
                MUSIC_ALREADYVOTEDTOSKIP
            )

    @app_commands.command(name="pause")
    @app_commands.check(check_member_in_vc)
    async def pause_cmd(self, inter:Inter):
        """Pauses the currently playing song"""

        voice_state = self.get_voice_state(inter)

        # Check that there is a song playing
        if not voice_state.is_playing:
            await inter.response.send_message(MUSIC_NOTPLAYING)
            return

        voice_state.voice.pause()
        await inter.response.send_message(MUSIC_PAUSED)

    @app_commands.command(name="resume")
    @app_commands.check(check_member_in_vc)
    async def resume_cmd(self, inter:Inter):
        """Resumes the currently playing song"""

        voice_state = self.get_voice_state(inter)

        # Check that there is a song playing
        if not voice_state.is_playing:
            await inter.response.send_message(MUSIC_NOTPLAYING)
            return

        voice_state.voice.resume()
        await inter.response.send_message(MUSIC_RESUMED)

    @app_commands.command(name="stop")
    @app_commands.check(check_member_in_vc)
    @app_commands.default_permissions(move_members=True)
    async def stop_cmd(self, inter:Inter):
        """Stops the music player and clears the queue"""

        log.debug("Stopping the music player")

        voice_state = self.get_voice_state(inter)
        voice_state.queue.clear()

        if voice_state.is_playing:
            await voice_state.stop()

        await inter.response.send_message(MUSIC_STOPPED)



    @app_commands.command(name="loop")
    @app_commands.check(check_member_in_vc)
    async def loop_cmd(self, inter:Inter, loop:bool):
        """Loops the currently playing song

        Args:
            loop (bool): True if the song should loop
        """

        voice_state = self.get_voice_state(inter)

        # We can't loop if there is no song playing
        if not voice_state.is_playing:
            await inter.response.send_message(MUSIC_NOTPLAYING)
            return

        # Set the loop state
        voice_state.loop = loop
        await inter.response.send_message(
            MUSIC_LOOPING if loop else MUSIC_NOTLOOPING
        )

    async def youtube_playback(self, inter:Inter, search:str):
        """Plays audio from a search query or URL, I will join the
           join the vc if the I'm not already in one.

        Args:
            search (str): The search query or URL to use
        """

        voice_state = self.get_voice_state(inter)

        # Join the voice channel if the bot is not already in one
        if not inter.guild.voice_client:
            await self.join_vc(inter)

        # This may take a while, defer to prevent timeout
        await inter.response.defer()

        # Create a source from the search query
        source = await YTDLSource.from_query(
            inter, search, async_loop=self.bot.loop
        )

        # Add the source to the queue as a Song
        song = Song(source)
        await voice_state.queue.put(song)

        # if the song is the only one in the queue, another embed
        # will be sent when the song starts playing, so don't clutter
        # the chat with this embed also.
        if voice_state.is_playing:
            embed = AddedTrackEmbed(
                song=song,
                voice_state=voice_state
            )
            view = TrackAddedView(song, voice_state)
            return await inter.followup.send(embed=embed, view=view)

        await inter.followup.send(MUSIC_ADDEDPLAYSOON)

    async def spotify_playback(self, inter:Inter, search:str):
        """Plays audio from a search query or URL, I will join the
           join the vc if the I'm not already in one.

        Args:
            search (str): The search query or URL to use
        """

        voice_state = self.get_voice_state(inter)

        # Join the voice channel if the bot is not already in one
        if not inter.guild.voice_client:
            await self.join_vc(inter)

        # This may take a while, defer to prevent timeout
        await inter.response.defer()

        # Create a source from the search query
        source = await SpotifySource.create_source(
            inter, search, loop=self.bot.loop
        )

        # Add the source to the queue as a Song
        song = Song(source)
        await voice_state.queue.put(song)

        # if the song is the only one in the queue, another embed
        # will be sent when the song starts playing, so don't clutter
        # the chat with this embed also.
        if voice_state.is_playing:
            embed = AddedTrackEmbed(
                song=song,
                voice_state=voice_state
            )
            view = TrackAddedView(song, voice_state)
            return await inter.followup.send(embed=embed, view=view)

        await inter.followup.send(MUSIC_ADDEDPLAYSOON)




    @app_commands.command(name="play")
    @app_commands.check(check_member_in_vc)
    async def play_audio_cmd(self, inter:Inter, source:Sources, search:str):
        """Plays audio from a search query or URL, I will join the
           join the vc if the I'm not already in one.

        Args:
            search (str): The search query or URL to use
        """

        await self.youtube_playback(inter, search)

    shortcut_group = app_commands.Group(
        name="youtube-shortcuts",
        description="Shortcuts for playback of certain youtube videos",
        guild_only=True
    )

    @shortcut_group.command(name="rickroll")
    @app_commands.check(check_member_in_vc)
    async def rickroll(self, inter:Inter):
        """Plays Rick Astley's "Never Gonna Give You Up" in the current"""

        await self.youtube_playback(inter, search="https://www.youtube.com/watch?v=dQw4w9WgXcQ")


    @shortcut_group.command(name="iamabadperson")
    @app_commands.check(check_member_in_vc)
    async def iamabadperson(self, inter:Inter):
        """Plays that one very annoying christmas song in the current"""

        await self.youtube_playback(inter, search="https://www.youtube.com/watch?v=aAkMkVFwAoo")

    @shortcut_group.command(name="2010youtube")
    @app_commands.check(check_member_in_vc)
    async def old_youtube(self, inter:Inter):
        """Plays a nostalgic track in the current voice channel"""

        await self.youtube_playback(inter, search="https://www.youtube.com/watch?v=Cm0qaXi9THA")
    
    @shortcut_group.command(name="deadmeme")
    @app_commands.check(check_member_in_vc)
    async def deadmeme(self, inter:Inter):
        """Plays a dead meme in the current voice channel"""

        await self.youtube_playback(inter, search="https://www.youtube.com/watch?v=LBnUc09MK2w")

    



async def setup(bot):
    """Setup function for the cog"""

    await bot.add_cog(MusicCog(bot))
