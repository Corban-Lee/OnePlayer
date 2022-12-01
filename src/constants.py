"""This file contains all the constants used in the bot."""

from easy_pil import Font


# Bot constants
ACTIVITY_MSG = 'I am up and running!'
DATE_FORMAT = '%d/%m/%Y'
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

# PronounDB constants
PRONOUNDB_GET_URL = "https://pronoundb.org/api/v1/lookup"
PRONOUNDB_LOGIN_URL = "https://pronoundb.org/login/"
PRONOUNDB_SET_URL = "https://pronoundb.org/me"

# Command constants
BDAY_HELP_MSG = 'Use `/birthday help` for more info'

# MSGS
BAD_TOKEN = 'You have passed an improper or invalid token! Shutting down...'
NO_TOKEN = 'TOKEN file not found in project root! Shutting down...'
NO_CONFIG = 'CRITICAL ERROR: config file is missing! Shutting down...'

# Logging constants
LOGS = 'logs/'
LOG_FILENAME_FORMAT_PREFIX = '%Y-%m-%d %H-%M-%S'
MAX_LOGFILE_AGE_DAYS = 7

# Levelcard constants
BLACK = "#0F0F0F"
WHITE = "#F9F9F9"
DARK_GREY = "#2F2F2F"
LIGHT_GREY = "#9F9F9F"
POPPINS = Font.poppins(size=70)
POPPINS_SMALL = Font.poppins(size=50)

# Messages/Words
ACTIVITY = "/help"
INVALID_PAGE_NUMBER = "Invalid page number! There are {} pages."
NO_TICKETS_ERR = (
    "This server does not have tickets enabled."
    "\nThey can be enabled by purposing a category for "
    "tickets if you have the manage channels permission."
)

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

# Entertainment constants

ROCK = "rock"
PAPER = "paper"
SCISSORS = "scissors"
RPS_CHOICES = (ROCK, PAPER, SCISSORS)
RPS_WINNER = "You win!"
RPS_LOSER = "You Lose, I win!"
RPS_DRAW = "Draw, we both chose the same thing..."
