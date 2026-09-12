import plistlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from web.icons.frames import IconKind

_IDLE_ANIMATIONS = {
    IconKind.ROBOT: "Robot_idle_001.png",
    IconKind.SPIDER: "Spider_idle_001.png",
}
_PART_PATTERN = re.compile(r"^(?:robot|spider)_\d+_(\d+)_001\.png$")


@dataclass(frozen=True, slots=True)
class PartPose:
    """Where one limb sits in the idle frame, in points at 1x scale."""

    part: int
    x: float
    y: float
    rotation: float
    scale_x: float
    scale_y: float
    flipped_x: bool
    flipped_y: bool
    z: int


def _pair(text: object, default: tuple[float, float]) -> tuple[float, float]:
    if not isinstance(text, str):
        return default

    parts = text.replace("{", "").replace("}", "").split(",")

    if len(parts) != 2:
        return default

    return float(parts[0]), float(parts[1])


def _pose(part: int, entry: dict[str, Any]) -> PartPose:
    x, y = _pair(entry.get("position"), (0.0, 0.0))
    scale_x, scale_y = _pair(entry.get("scale"), (1.0, 1.0))
    flipped_x, flipped_y = _pair(entry.get("flipped"), (0.0, 0.0))

    return PartPose(
        part=part,
        x=x,
        y=y,
        rotation=float(entry.get("rotation", 0.0)),
        scale_x=scale_x,
        scale_y=scale_y,
        flipped_x=flipped_x != 0,
        flipped_y=flipped_y != 0,
        z=int(entry.get("zValue", 0)),
    )


def load_poses(plist: Path, kind: IconKind) -> list[PartPose] | None:
    """The idle pose of the animation description the game ships. `None`
    when the file is absent or shaped unexpectedly."""

    animation_name = _IDLE_ANIMATIONS.get(kind)

    if animation_name is None or not plist.is_file():
        return None

    with plist.open("rb") as handle:
        data = plistlib.load(handle)

    container = data.get("animationContainer")

    if not isinstance(container, dict):
        return None

    frame = container.get(animation_name)

    if not isinstance(frame, dict):
        return None

    poses = []

    for name, entry in frame.items():
        match = _PART_PATTERN.match(str(name))

        if match is None or not isinstance(entry, dict):
            continue

        poses.append(_pose(int(match.group(1)), entry))

    if not poses:
        return None

    return sorted(poses, key=lambda pose: pose.z)
