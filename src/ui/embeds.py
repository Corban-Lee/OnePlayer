"""Embeds for the project"""

import logging
from datetime import datetime, timedelta

import discord


log = logging.getLogger(__name__)


class MusicQueueEmbed(discord.Embed):
    """Embed for showing the music queue"""

    def __init__(
        self,
        description: str,
        current_page: int,
        total_pages: int
    ):
        super().__init__(
            description=description,
            color=discord.Color.blurple()
        )
        self.set_footer(text=f"Page {current_page}/{total_pages}")


class NowPlayingEmbed(discord.Embed):
    """Embed for when a track starts playing"""

    def __init__(self, song):

        log.debug("Creating NowPlayingEmbed")

        super().__init__(
            title="Now Playing",
            colour=discord.Colour.blurple()
        )

        # Shorthand for the source object
        src = song.source

        self.set_thumbnail(url=src.thumbnail)

        self.description = (
            f"[**{src.title}**]({src.url})"

            f"\n\n**By** [{src.uploader}]({src.uploader_url})"
            f"\n**Requested by:** {src.requester.mention}"
            f"\n**Duration:** *{src.parsed_duration}*"
        )


class AddedTrackEmbed(discord.Embed):
    """Embed displayed when a track is added to the queue"""

    def __init__(self, song, voice_state):

        log.debug("Creating AddedTrackEmbed")

        super().__init__(
            title="Track Added to Queue",
            colour=discord.Colour.blurple()
        )

        self.set_thumbnail(url=song.source.thumbnail)

        # Get the song's position in the queue
        position = voice_state.queue.index(song) + 1 

        # Get the estimated time the song will play
        time_until_played = self._get_time_until_played(
            song, voice_state
        )

        # Set the embed's description
        self.description = (
            f"[**{song.source.title}**]({song.source.url})"

            f"\n\n**By** [{song.source.uploader}]({song.source.uploader_url})"
            f"\n**Requested by:** {song.source.requester.mention}"

            f"\n\n**Duration:** *{song.source.parsed_duration}*"
            f"\n**Position in queue:** {position}"
            f"\n**Will play:** {time_until_played}"
        )

    def _get_time_until_played(self, song, voice_state) -> str:
        """Get the time until the song will be played

        Args:
            song (Song): The song to get the time for
            voice_state (VoiceState): The voice state of the bot

        Returns:
            str: The time until the song will be played
                (discord timestamp or "Now Playing")
        Raises:
            ValueError: If the song is not in the queue
            AssertionError: Should never be raised
        """

        log.debug("Getting time until song will be played")

        # If the song is the first in the queue and there is a
        # current song: The song will be played after the current.
        if voice_state.queue[0] == song:
            log.debug("Song is first in queue and there is a current song")

            if voice_state.current.source.duration == 0:
                log.debug("Current song is a livestream")
                return "*Unknown because a livestream is playing*"

            est_time = datetime.now() + timedelta(
                seconds=voice_state.current.source.duration
            )
            return f"<t:{int(est_time.timestamp())}:R>"

        # Get the duration of all songs in the queue before the
        # passed song.
        duration_sum = voice_state.current.source.duration

        if not duration_sum:
            log.debug("livesteam in queue, cant calculate duration")
            return "*Unknown because a livestream is playing*"

        for track in voice_state.queue:

            # There is a livestream in the queue before the song.
            # The duration of the song cannot be calculated.
            if not track.source.duration and track != song:
                log.debug("livesteam in queue, cant calculate duration")
                return "*Unknown because a livestream is in the queue*"

            # We found the song in the queue, we don't want to
            # count the duration of any more songs now.
            if track == song:
                est_time = datetime.now() + timedelta(
                    seconds=duration_sum
                )
                log.debug(f"Found song in queue, {est_time=}")
                return f"<t:{int(est_time.timestamp())}:R>"

            # Add the duration of the song to the duration sum
            duration_sum += track.source.duration
            log.debug("Added song duration to duration sum")

        # If we get here, the song is not in the queue,
        # this is a problem.
        raise ValueError("Song not in queue")
