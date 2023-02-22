"""Extension for music commands"""

import asyncio

import discord
from discord import (
    app_commands,
    Interaction as Inter,
    
)
from discord.utils import get
import youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from . import BaseCog
from utils import edit_original


# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ''


class YTDLSource(discord.PCMVolumeTransformer):
    """Represents a youtube video source"""

    ytdl = youtube_dl.YoutubeDL()

    def __init__(self, source, data, volume=.5):
        super().__init__(source, volume)

        self.data = data
        # self.source = source
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def create_source(cls, inter:Inter, url_or_search:str, *, loop=None, stream:bool=True, ytdl_format:dict=None):
        """Create a source from a url or search query"""

        loop = loop or asyncio.get_event_loop()

        # Add search prefix if using a search query over a url
        if not "youtube.com" in url_or_search:
            url_or_search = f"ytsearch:{url_or_search}"

        data = await loop.run_in_executor(
            None,
            lambda: youtube_dl.YoutubeDL(ytdl_format).extract_info(url_or_search, download=not stream)
        )

        if 'entries' in data:
            data = data['entries'][0]

        formats = data.get('formats', [data])
        audio_url = None
        for f in formats:
            if f.get("acodec") == "opus":
                audio_url = f.get("url")
                break

        if audio_url is None:
            raise ValueError("No audio stream found.")

        return cls(discord.FFmpegPCMAudio(audio_url, options='-vn'), data=data)

    async def wait_for_download(self):
        while not self.source.is_loaded():
            await asyncio.sleep(1)

    async def cancel_download(self):
        await self._cleanup()

    async def _cleanup(self):
        self.data = None
        await self.source.cleanup()


class SpotifySource(discord.PCMVolumeTransformer):
    """Represents a spotify song source"""




class MusicCog(BaseCog, name="New Music"):
    """Cog for music commands"""

    ytdl_format_options = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'
    }

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="play")
    async def cmd_play(self, inter:Inter, search: str):
        """Play's music in the current voice channel"""

        if not inter.user.voice:
            await inter.response.send_message("You aren't in a voice channel.")
            return

        channel = inter.user.voice.channel
        voice: discord.VoiceClient = get(self.bot.voice_clients, guild=inter.guild)

        # If the voice channel is already playing, stop the previous track
        if voice and voice.is_playing():
            voice.stop()

        # If not in a voice channel, join the user
        elif not voice:
            voice = await channel.connect()

        # If in a different voice channel, move to join the user
        else:
            await voice.move_to(channel)

        await inter.response.send_message("Searching for track ...")

        # Get the video source
        try:
            source = await YTDLSource.create_source(inter, search, loop=self.bot.loop)
        except Exception as error:
            await edit_original(f"An error occured while processing this request: `{error}`")
            return

        voice.play(source, after=lambda e: print(f"Finished playing track"))
        await edit_original(f"Now playing {source.title}")

        # Halt the command until the audio is finished
        while voice.is_playing() or voice.is_paused():
            await asyncio.sleep(1)

        # The track is finished, inform the user
        await inter.edit_original_response(content="Finished playing track.")

    @app_commands.command(name="pause")
    async def cmd_pause(self, inter:Inter):
        """Pause the current track"""

        await inter.response.defer()

        voice = get(self.bot.voice_clients, guild=inter.guild)
        if voice and voice.is_playing:
            voice.pause()
            await edit_original("Current track paused.")
            return

        await edit_original("No music is playing right now.")

    @app_commands.command(name="resume")
    async def cmd_resume(self, inter:Inter):
        """Resume the currently paused track"""

        await inter.response.defer()

        voice = get(self.bot.voice_clients, guild=inter.guild)
        if voice and voice.is_paused():
            voice.resume()
            await edit_original("Resuming track.")

        elif voice and voice.is_playing():
            await edit_original("Audio is not paused.")

        else:
            await edit_original("No tracks playing at the moment.")


async def setup(bot):
    """Setup function for the cog"""

    await bot.add_cog(MusicCog(bot))
