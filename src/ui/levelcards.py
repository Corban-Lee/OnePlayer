"""Levelcards module. Contains the Levelcard class and related functions."""

import logging
from math import ceil
from functools import cache
from time import perf_counter

from discord import Status, Colour, Member, File
from easy_pil import (
    Editor,
    Canvas,
    Text,
    load_image_async
)
from PIL import Image

from db import MemberLevelModel
from constants import (
    WHITE,
    BLACK,
    LIGHT_GREY,
    DARK_GREY,
    POPPINS,
    POPPINS_SMALL
)


log = logging.getLogger(__name__)


@cache
def get_status_colour(status:Status) -> Colour:
    """Get the colour that corresponds to the given status

    Args:
        status (discord.Status): The status to get the colour for

    Returns:
        discord.Colour: The colour that corresponds to the given

    Raises:
        ValueError: If the status is not recognised
    """

    log.debug("Getting colour for status %s", status)

    match status:
        case Status.online:
            return Colour.green()
        case Status.idle:
            return Colour.dark_gold()
        case Status.dnd:
            return Colour.red()
        case Status.offline:
            return Colour.light_grey()
        case Status.invisible:
            return Colour.blurple()
        case _:
            raise ValueError(f"Unknown Status: {status}")

@cache
def get_colours(dark_mode:bool) -> tuple[str, str, str, str]:
    """Get the colours for the levelboard
    Returns the colours as a tuple in the following order:
        background1, background2, foreground1, foreground2

    Args:
        dark_mode (bool): Whether the levelboard is in dark mode

    Returns:
        tuple[str, str, str, str]: The colours for the levelboard
    """

    log.debug("Getting colours for levelcard, darkmode=%s", dark_mode)

    if dark_mode:
        return BLACK, DARK_GREY, WHITE, LIGHT_GREY

    return WHITE, LIGHT_GREY, BLACK, DARK_GREY


class CustomImageBase:
    """Base class for custom images"""

    __slots__ = ()
    editor: Editor
    member: Member

    # Colours
    is_darkmode: bool
    _foreground_1: str
    _foreground_2: str
    _background_1: str
    _background_2: str
    _accent_colour:str
    _status_colour:str

    def define_colours(self):
        """Define the colours for the card"""

        log.debug("Defining colours")

        # Set attributes for the colours
        (self._background_1,
         self._background_2,
         self._foreground_1,
         self._foreground_2) = get_colours(self.is_darkmode)

        # Set the status colour
        self._status_colour = get_status_colour(
            self.member.status
        ).to_rgb()

        # The default colour is black, catch that here and swap it
        # out for light grey
        if self.member.colour == Colour.default():
            self._accent_colour = Colour.light_grey().to_rgb()
            return

        # Otherwise just set the accent to the member's colour
        self._accent_colour = self.member.colour.to_rgb()

    def antialias_resize(self):
        """Halves the width and height of the image, but the image
        will be antialiased to make it look smoother"""

        start = perf_counter()
        log.debug("Resizing and antialiasing the image")

        image = self.editor.image
        new_size = tuple(i//2 for i in image.size)
        self.editor = Editor(image.resize(
            size=new_size,
            resample=Image.ANTIALIAS
        ))

        end = perf_counter()
        log.debug(
            "Resizing and antialiasing took %s seconds",
            end-start
        )

    def get_file(self, filename:str=None) -> File:
        """Get the card as a discord.File object. Filename defaults to
        "<memberid>_levelcard.png"

        Args:
            filename (str, optional): Overwrite the default filename.

        Returns:
            discord.File: The card as a discord.File
        """

        return File(
            self.editor.image_bytes,
            filename=filename or "onebot_image.png",
            description="An image created by OneBot."
        )

class LevelUpCard(CustomImageBase):
    """A ranking card for members"""

    __slots__ = ("is_darkmode", "editor")
    lvl_obj: MemberLevelModel
    member: Member

    def __init__(
        self, member:Member, lvl_obj:MemberLevelModel, is_darkmode:bool=True
    ):

        log.info("Creating new level up card")

        self.member = member
        self.lvl_obj = lvl_obj
        self.is_darkmode = is_darkmode

    async def draw(self):
        """Draw the level card for the member

        Returns:
            LevelCard: The same instance of the levelcard
        """

        log.debug("Drawing levelcard")

        # The colours are used in the rest of the drawing process,
        # so it's important to define them first
        self.define_colours()

        # The card is the main image that is drawn on
        self.editor = Editor(
            Canvas(
                (1800, 200),
                color=self._background_1
            )
        ).rounded_corners(100)

        # The card is resized to half its size to antialias it
        self.antialias_resize()

        log.debug("Finished drawing levelcard, returning")

        return self


class ScoreBoard(CustomImageBase):
    """Scoreboard class. Creates a scoreboard image for each member"""

    slots = ("members",)

    def __init__(self, members:tuple[tuple[Member, MemberLevelModel]]):
        self.members = members

    async def draw(self):
        """Draw the scoreboard"""

        log.info("Drawing scoreboard")

        width = 920 * len(self.members) if len(self.members) < 3  else 2760
        height = 220 * ceil(len(self.members) / 3) if len(self.members) >= 3 else 220
        x_pos = y_pos = 0

        self.editor = Editor(Canvas((width, height)))

        for i, (member, lvl_obj) in enumerate(self.members):

            log.debug("%s is at position %sx%s", i, x_pos, y_pos)

            card = LevelCard(member, lvl_obj)
            await card.draw()
            self.editor.paste(card.editor, (x_pos, y_pos))

            i += 1
            if i % 3 != 0:
                x_pos += 920
            # every fourth card is on a new row
            else:
                x_pos = 0
                y_pos += 220

        self.editor.image = self.editor.image.crop((0, 0, width-20, height-20))

class LevelCard(CustomImageBase):
    """A ranking card for members"""

    __slots__ = (
        "lvl_obj", "member", "is_darkmode",
        "_foreground_1",
        "_foreground_2",
        "_background_1",
        "_background_2",
        "_accent_colour",
        "_status_colour",
        "editor"
    )

    def __init__(
        self, member:Member, lvl_obj:MemberLevelModel,
        is_darkmode:bool=True
    ):
        """Create a new LevelCard"""

        log.info("Creating new levelcard")

        self.member = member
        self.lvl_obj = lvl_obj
        self.is_darkmode = is_darkmode

    async def draw(self):
        """Draw the level card"""

        start = perf_counter()
        log.debug("Drawing levelcard")

        # The colours are used in the rest of the drawing process,
        # so it's important to define them first
        self.define_colours()

        # The card is the main image that is drawn on
        self.editor = Editor(
            Canvas(
                (1800, 400),
                color=self._background_1
            )
        )

        # Draw the various elements of the card
        self._draw_accent_polygon()
        await self._draw_avatar()
        self._draw_status_icon()
        self._draw_progress_bar()
        self._draw_name()
        self._draw_exp()
        self._draw_levelrank()

        self.editor.rounded_corners(20)

        # The card is resized to half its size to antialias it
        self.antialias_resize()

        end = perf_counter()
        log.debug("Took %s seconds to draw levelcard", end-start)

        return self

    def _draw_accent_polygon(self):
        """Draw the accent colour polygon on the card"""

        start = perf_counter()
        log.debug("Drawing accent polygon")

        self.editor.polygon(
            (
                (2, 2),  # top left
                (2, 360),  # bottom left
                (360, 2),  # bottom right
                (2, 2)  # top right
            ),
            fill=self._accent_colour
        )

        end = perf_counter()
        log.debug(
            "Finished drawing accent polygon in %s seconds",
            end-start
        )

    async def _draw_avatar(self):
        """Draw the avatar on the card"""

        start = perf_counter()
        log.debug("Drawing avatar image")

        # Get the member's avatar as an Image object
        avatar = await load_image_async(self.member.display_avatar.url)

        # Shape the avatar into a circle with a border
        avatar_image = Editor(Canvas(
            (320, 320),
            color=self._background_1
        )).circle_image().paste(
            Editor(avatar).resize((300, 300)).circle_image(),
            (10, 10)
        )

        # Paste the avatar onto the card
        self.editor.paste(avatar_image, (40, 40))

        end = perf_counter()
        log.debug(
            "Finished drawing avatar image in %s seconds",
            end-start
        )

    def _draw_status_icon(self):
        """Draw the status icon on the card"""

        start = perf_counter()
        log.debug("Drawing status icon")

        status_image = Editor(Canvas(
            (90, 90),
            color=self._background_1
        )).circle_image().paste(
            Editor(Canvas(
                (70, 70),
                color=self._status_colour
            )).circle_image(),
            (10, 10)
        )

        log.debug("Drawing status icon symbol")

        match self.member.status:

            case Status.idle:
                status_image.paste(Editor(Canvas(
                    (50, 50),
                    color=self._background_1
                )).circle_image(), (5, 10))

            case Status.dnd:
                status_image.rectangle(
                    (20, 39), width=50, height=12,
                    fill=self._background_1, radius=15
                )

            case Status.offline:
                status_image.paste(Editor(Canvas(
                    (40, 40),
                    color=self._background_1
                )).circle_image(), (25, 25))

            case _:
                pass

        # Paste the status icon onto the card
        self.editor.paste(status_image, (260, 260))

        end = perf_counter()
        log.debug(
            "Finished drawing status icon in %s seconds", end-start
        )

    def _draw_progress_bar(self):
        """Draw the progress bar"""

        start = perf_counter()
        log.debug("Drawing progress bar")

        # Bar dimensions
        position = (420, 275)
        width = 1320
        height = 60
        radius = 40

        # The trough for the bar background
        self.editor.rectangle(
            position=position,
            width=width, height=height,
            color=self._background_2,
            radius=radius
        )

        # The bar itself, dynamically changes based on the member's xp
        self.editor.bar(
            position=position,
            max_width=width, height=height,
            color=self._accent_colour,
            percentage=max(self.lvl_obj.percentage_to_next, 5),
            radius=radius
        )

        end = perf_counter()
        log.debug(
            "Finished drawing progress bar in %s seconds",
            end-start
        )

    def _draw_name(self):
        """Draw the member's name on the card"""

        start = perf_counter()
        log.debug("Drawing name text")

        # Shorthands for the name and discriminator
        name = self.member.display_name
        discriminator = f"#{self.member.discriminator}"

        # Prevent the name text from overflowing
        if len(name) > 15:
            log.debug("Name is too long, shortening")
            name = name[:15]

        # Draw it right onto the card
        self.editor.multi_text(
            position=(420, 220),  # bottom left
            texts=(
                Text(
                    name,
                    font=POPPINS,
                    color=self._foreground_1
                ),
                Text(
                    discriminator,
                    font=POPPINS_SMALL,
                    color=self._foreground_2
                )
            )
        )

        end = perf_counter()
        log.debug(
            "Finished drawing name text in %s seconds",
            end-start
        )

    def _draw_exp(self):
        """Draw the exp and next exp on the card"""

        start = perf_counter()
        log.debug("Drawing exp text")

        # Draw it right onto the card
        self.editor.multi_text(
            position=(1740, 225),  # bottom right
            align="right",
            texts=(
                Text(
                    self.lvl_obj.xp,
                    font=POPPINS_SMALL,
                    color=self._foreground_1
                ),
                Text(
                    f"/ {self.lvl_obj.next_xp} XP",
                    font=POPPINS_SMALL,
                    color=self._foreground_2
                )
            )
        )

        end = perf_counter()
        log.debug(
            "Finished drawing exp text in %s seconds",
            end-start
        )

    def _draw_levelrank(self):
        """Draw the level and rank on the card"""

        start = perf_counter()
        log.debug("Drawing level and rank text")

        self.editor.multi_text(
            position=(1700, 80),  # top right
            align="right",
            texts=(
                Text(
                    "RANK",
                    font=POPPINS_SMALL,
                    color=self._foreground_2
                ),
                Text(
                    f"#{self.lvl_obj.rank} ",
                    font=POPPINS,
                    color=self._accent_colour
                ),
                Text(
                    "LEVEL",
                    font=POPPINS_SMALL,
                    color=self._foreground_2
                ),
                Text(
                    str(self.lvl_obj.level),
                    font=POPPINS,
                    color=self._accent_colour
                )
            )
        )

        end = perf_counter()
        log.debug(
            "Finished drawing level and rank text in %s seconds",
            end-start
        )
