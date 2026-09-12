from dataclasses import dataclass
from enum import StrEnum

from gdformat.enums import IconType


class IconKind(StrEnum):
    CUBE = "cube"
    SHIP = "ship"
    BALL = "ball"
    UFO = "ufo"
    WAVE = "wave"
    ROBOT = "robot"
    SPIDER = "spider"
    SWING = "swing"
    JETPACK = "jetpack"


class Tint(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    GLOW = "glow"
    WHITE = "white"


@dataclass(frozen=True, slots=True)
class Layer:
    name: str
    tint: Tint
    # Only the primary layer must exist; the others are decoration.
    required: bool = False


_PREFIXES = {
    IconKind.CUBE: "player",
    IconKind.SHIP: "ship",
    IconKind.BALL: "player_ball",
    IconKind.UFO: "bird",
    IconKind.WAVE: "dart",
    IconKind.ROBOT: "robot",
    IconKind.SPIDER: "spider",
    IconKind.SWING: "swing",
    IconKind.JETPACK: "jetpack",
}

_ANIMATED = frozenset({IconKind.ROBOT, IconKind.SPIDER})


def from_icon_type(icon_type: IconType) -> IconKind:
    match icon_type:
        case IconType.CUBE:
            return IconKind.CUBE
        case IconType.SHIP:
            return IconKind.SHIP
        case IconType.BALL:
            return IconKind.BALL
        case IconType.UFO:
            return IconKind.UFO
        case IconType.WAVE:
            return IconKind.WAVE
        case IconType.ROBOT:
            return IconKind.ROBOT
        case IconType.SPIDER:
            return IconKind.SPIDER
        case IconType.SWING:
            return IconKind.SWING
        case IconType.JETPACK:
            return IconKind.JETPACK


def prefix(kind: IconKind) -> str:
    return _PREFIXES[kind]


def is_animated(kind: IconKind) -> bool:
    return kind in _ANIMATED


def sheet_name(kind: IconKind, icon_id: int) -> str:
    return f"{prefix(kind)}_{icon_id:02d}"


def layers(kind: IconKind, icon_id: int) -> list[Layer]:
    """Bottom to top, glow first. The UFO's dome sits between the glow and the
    coloured body."""

    base = sheet_name(kind, icon_id)
    stack = [Layer(f"{base}_glow_001.png", Tint.GLOW)]

    if kind is IconKind.UFO:
        stack.append(Layer(f"{base}_3_001.png", Tint.WHITE))

    stack.append(Layer(f"{base}_2_001.png", Tint.SECONDARY))
    stack.append(Layer(f"{base}_001.png", Tint.PRIMARY, required=True))
    stack.append(Layer(f"{base}_extra_001.png", Tint.WHITE))

    return stack


def part_layers(kind: IconKind, icon_id: int, part: int) -> list[Layer]:
    """A robot or spider limb, named like `robot_01_02_001.png`."""

    base = f"{sheet_name(kind, icon_id)}_{part:02d}"

    return [
        Layer(f"{base}_glow_001.png", Tint.GLOW),
        Layer(f"{base}_2_001.png", Tint.SECONDARY),
        Layer(f"{base}_001.png", Tint.PRIMARY, required=True),
        Layer(f"{base}_extra_001.png", Tint.WHITE),
    ]
