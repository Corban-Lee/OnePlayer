"""Exceptions for the project"""


class EmptyQueryResult(Exception):
    """The query returned no results"""

class VoiceError(Exception):
    """An error occured in the voice client"""

class YTDLError(Exception):
    """An error occured while fetching data from YouTube"""
