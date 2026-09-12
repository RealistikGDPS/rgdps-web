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
_BACK_PREFIX = "back"


@dataclass(frozen=True, slots=True)
class PartPose:
    """Where one limb sits in the idle frame, in points at 1x scale. The
    same limb sprite is placed several times (both legs share one texture);
    `back` marks the copies the game draws darker behind the body."""

    part: int
    back: bool
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


def _back_tags(data: dict[str, Any]) -> set[str]:
    textures = data.get("usedTextures")

    if not isinstance(textures, dict):
        return set()

    return {
        str(entry["tag"])
        for entry in textures.values()
        if isinstance(entry, dict)
        and str(entry.get("customID", "")).startswith(_BACK_PREFIX)
    }


def _pose(entry: dict[str, Any], back_tags: set[str]) -> PartPose | None:
    match = _PART_PATTERN.match(str(entry.get("texture", "")))

    if match is None:
        return None

    x, y = _pair(entry.get("position"), (0.0, 0.0))
    scale_x, scale_y = _pair(entry.get("scale"), (1.0, 1.0))
    flipped_x, flipped_y = _pair(entry.get("flipped"), (0.0, 0.0))

    return PartPose(
        part=int(match.group(1)),
        back=str(entry.get("tag", "")) in back_tags,
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

    # The game ships these with a blank line before the XML header, which
    # plistlib's format sniffing does not tolerate.
    data = plistlib.loads(plist.read_bytes().lstrip())
    container = data.get("animationContainer")

    if not isinstance(container, dict):
        return None

    frame = container.get(animation_name)

    if not isinstance(frame, dict):
        return None

    back_tags = _back_tags(data)
    poses = []

    for entry in frame.values():
        if not isinstance(entry, dict):
            continue

        pose = _pose(entry, back_tags)

        if pose is not None:
            poses.append(pose)

    if not poses:
        return None

    return sorted(poses, key=lambda pose: pose.z)
