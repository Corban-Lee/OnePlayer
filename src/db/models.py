"""Database object models"""

import sqlite3
import logging
from dataclasses import dataclass
from math import sqrt, ceil
from enum import Enum

from utils import abbreviate_num
from exceptions import EmptyQueryResult
from . import db


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class GuildChannels:
    """Dataclass for guild channel data"""

    channel_id: int
    guild_id: int
    purpose_id: int

    @classmethod
    def from_purpose(cls, guild_id:int, purpose_id:int):
        """Get a GuildChannels object from a guild id and purpose id"""

        data = db.record(
            "SELECT * FROM guild_channels WHERE guild_id = ? AND purpose_id = ?",
            guild_id, purpose_id
        )
        if not data:
            raise EmptyQueryResult("No channel found for purpose")

        channel_id, _, _ = data
        return cls(
            channel_id=channel_id,
            guild_id=guild_id,
            purpose_id=purpose_id
        )

    @classmethod
    def from_database(cls, channel_id:int):
        """Get a GuildChannels object from a channel id"""

        data = db.record(
            "SELECT * FROM guild_channels WHERE channel_id = ?",
            channel_id
        )
        if not data:
            raise EmptyQueryResult("No channel found with that id")

        _, guild_id, purpose_id = data
        return cls(
            channel_id=channel_id,
            guild_id=guild_id,
            purpose_id=purpose_id
        )


@dataclass
class MemberLevelModel:
    """Dataclass to store member level data"""

    member_id: int
    guild_id: int
    xp_raw: int

    def __post_init__(self):
        self._update()
        log.debug("Created MemberLevelModel Instance")

    def _update(self):
        self.level_raw = 0.07 * sqrt(self.xp_raw)
        self.prev_xp_raw = (ceil(self.level_raw - 1) /0.07) ** 2
        self.next_xp_raw = (ceil(self.level_raw) / 0.07) ** 2

    @property
    def xp(self) -> str:  # pylint: disable=invalid-name
        """Get the member experience points"""

        log.debug("Getting member xp")
        return abbreviate_num(self.xp_raw - self.prev_xp_raw - 1)

    @property
    def next_xp(self) -> int:
        """Get the member experience points needed for the next level"""

        log.debug("Getting member next xp")
        return abbreviate_num(self.next_xp_raw - self.prev_xp_raw - 1)

    @property
    def prev_xp(self):
        """Get the member experience points needed for the previous level"""

        log.debug("Getting member prev xp")
        return abbreviate_num(self.prev_xp_raw - 1)

    @property
    def total_xp(self):
        """Get the total xp of this member"""

        log.debug("Getting total xp")
        return abbreviate_num(self.xp_raw)

    @property
    def total_next_xp(self):
        """Get the total xp needed for the next level"""

        log.debug("Getting total next xp")
        return abbreviate_num(self.next_xp_raw)

    @property
    def percentage_to_next(self) -> float:
        """Get the percentage of xp to the next level"""

        return (
            (self.xp_raw - self.prev_xp_raw) /
            (self.next_xp_raw - self.prev_xp_raw)
        ) * 100

    @property
    def level(self) -> int:
        """Get the member level"""

        log.debug("Getting member level")
        return ceil(self.level_raw)

    @property
    def rank(self) -> int:
        """Get the member rank"""

        log.debug("Getting member rank")
        rank = db.field(
            """SELECT rank FROM (
             SELECT member_id, RANK() OVER ( ORDER BY experience DESC )
             AS rank
             FROM member_levels WHERE guild_id = ?
            ) WHERE member_id = ?
            """,
            self.guild_id, self.member_id
        )
        if rank is None:
            return "?"

        return rank

    def set_xp(self, new_xp:int) -> None:
        """Set the xp of this object

        Args:
            new_xp (int): The new xp to set
        """

        log.debug("Setting xp to %s", new_xp)
        self.xp_raw = int(new_xp)
        self._update()

    def savenew(self, commit:bool=False) -> None:
        """Save this model to the database"""

        log.debug("Saving MemberLevelModel")
        db.execute(
            "INSERT INTO member_levels (member_id, guild_id) "
            "VALUES (?, ?)",
            self.member_id, self.guild_id
        )
        if commit:
            db.commit()

    def update(self, commit:bool=False) -> None:
        """Save this model to the database"""

        log.debug("Saving MemberLevelModel")
        db.execute(
            "UPDATE member_levels SET experience = ? "
            "WHERE member_id=? AND guild_id=?",
            self.xp_raw, self.member_id, self.guild_id
        )
        if commit:
            db.commit()

    def delete(self, commit:bool=False) -> None:
        """Delete this model from the database"""

        log.debug("Deleting MemberLevelModel")
        db.execute(
            "DELETE FROM member_levels WHERE member_id=? AND guild_id=?",
            self.member_id, self.guild_id
        )
        if commit:
            db.commit()

    @classmethod
    def from_database(cls, member_id: int, guild_id:int):
        """Create the object from database data"""

        log.debug("Creating MemberLevelModel from database")
        xp = db.field(
            "SELECT experience FROM member_levels " \
            "WHERE member_id = ? AND guild_id = ?",
            member_id, guild_id
        )
        if not xp:
            raise EmptyQueryResult(
                "There is no data for member with id "
                f"{member_id} in guild with id {guild_id}"
            )

        return cls(member_id, guild_id, xp)

## forgot what this is
## afraid to touch 😀
class UserSettings:

    def get(user_id:int, option:Enum) -> bool:
        """Get a user setting"""

        log.debug("Getting user setting")

        try:
            return bool(db.field(
                "SELECT value FROM settings_options "
                "WHERE object_id = ? AND option_id = ?",
                user_id, option.value
            ))
        except sqlite3.IntegrityError:
            log.debug("Setting not found")
            return None
