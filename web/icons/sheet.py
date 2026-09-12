import plistlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image


@dataclass(frozen=True, slots=True)
class Frame:
    x: int
    y: int
    width: int
    height: int
    offset_x: int
    offset_y: int
    source_width: int
    source_height: int
    rotated: bool


def _numbers(text: str) -> list[int]:
    """Cocos2d writes rectangles and points as `{{x,y},{w,h}}` and `{x,y}`."""

    return [
        int(float(part)) for part in text.replace("{", "").replace("}", "").split(",")
    ]


def _frame(entry: dict[str, Any]) -> Frame:
    x, y, width, height = _numbers(str(entry["textureRect"]))
    offset_x, offset_y = _numbers(str(entry["spriteOffset"]))
    source_width, source_height = _numbers(str(entry["spriteSourceSize"]))

    return Frame(
        x=x,
        y=y,
        width=width,
        height=height,
        offset_x=offset_x,
        offset_y=offset_y,
        source_width=source_width,
        source_height=source_height,
        rotated=bool(entry.get("textureRotated", False)),
    )


class SpriteSheet:
    """One texture atlas and its frames, as the game ships them."""

    __slots__ = ("_frames", "_image")

    def __init__(self, image: Image.Image, frames: dict[str, Frame]) -> None:
        self._image = image
        self._frames = frames

    def has(self, name: str) -> bool:
        return name in self._frames

    def crop(self, name: str) -> Image.Image | None:
        """The sprite trimmed by the packer, restored onto its untrimmed canvas
        so every layer of one icon lines up."""

        frame = self._frames.get(name)

        if frame is None:
            return None

        if frame.rotated:
            box = (frame.x, frame.y, frame.x + frame.height, frame.y + frame.width)
            sprite = self._image.crop(box).rotate(90, expand=True)
        else:
            box = (frame.x, frame.y, frame.x + frame.width, frame.y + frame.height)
            sprite = self._image.crop(box)

        canvas = Image.new("RGBA", (frame.source_width, frame.source_height))
        left = (frame.source_width - frame.width) // 2 + frame.offset_x
        top = (frame.source_height - frame.height) // 2 - frame.offset_y
        canvas.paste(sprite, (left, top))

        return canvas


def load_sheet(png: Path, plist: Path) -> SpriteSheet | None:
    if not png.is_file() or not plist.is_file():
        return None

    with plist.open("rb") as handle:
        data = plistlib.load(handle)

    entries = data.get("frames")

    if not isinstance(entries, dict):
        return None

    frames = {str(name): _frame(entry) for name, entry in entries.items()}

    with Image.open(png) as image:
        loaded = image.convert("RGBA")

    return SpriteSheet(loaded, frames)
