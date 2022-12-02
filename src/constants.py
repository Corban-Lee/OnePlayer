"""This file contains all the constants used in the bot."""

# Bot constants
ACTIVITY_MSG = 'I am up and running!'
DATE_FORMAT = '%d/%m/%Y'
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

# MSGS
BAD_TOKEN = 'You have passed an improper or invalid token! Shutting down...'
NO_TOKEN = 'TOKEN file not found in project root! Shutting down...'
NO_CONFIG = 'CRITICAL ERROR: config file is missing! Shutting down...'

# Logging constants
LOGS = 'logs/'
LOG_FILENAME_FORMAT_PREFIX = '%Y-%m-%d %H-%M-%S'
MAX_LOGFILE_AGE_DAYS = 7

# Messages/Words
ACTIVITY = "/help"
INVALID_PAGE_NUMBER = "Invalid page number! There are {} pages."

MUSIC_CANTLEAVEVC = (
    "I can't leave the voice channel if I'm not in one!"
    "\nUse `/music join` to make me join a voice channel."
)
MUSIC_BOTNOTINVC = (
    "I'm not in a voice channel!"
    "\nUse `/music join` to make me join a voice channel."
)
MUSIC_USERNOTINVC = (
    "You're not in a voice channel!"
    "\nJoin a voice channel and try again."
)
MUSIC_NOTPLAYING = "I'm not playing anything right now!"
MUSIC_QUEUEEMPTY = (
    "The queue is empty!"
    "\nUse `/music play` to add songs to the queue."
)
MUSIC_BOTDIFFVC = (
    "I'm already in a voice channel!"
    "\nJoin the same voice channel as me and try again."
)
MUSIC_JOINEDVC = (
    "I've Joined the voice channel!"
    "\nUse `/music play` to add songs to the queue."
)
MUSIC_LEFTVC = "I've left the voice channel! :wave:"
MUSIC_SKIPPEDSONG = "I skipped the song for you :thumbsup:"
MUSIC_SKIPVOTEREGISTERED = (
    "You have registered your vote to skip the song!"
    "\n**{}** more votes are needed to skip the song."
)
MUSIC_ALREADYVOTEDTOSKIP = "You have already voted to skip the song!"
MUSIC_RESUMED = "I've resumed the song for you :thumbsup:"
MUSIC_PAUSED = "I've paused the song for you :thumbsup:"
MUSIC_STOPPED = "I've stopped the music player"
MUSIC_LOOPING = "I've enabled looping for this song!"
MUSIC_NOTLOOPING = "I've disabled looping for this song!"
MUSIC_ADDEDPLAYSOON = (
    "I've added the song to the queue!"
    "\nIt will play in a moment."
)
