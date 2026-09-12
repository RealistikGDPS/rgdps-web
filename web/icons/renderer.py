import io
from collections import OrderedDict
from dataclasses import dataclass
from enum import StrEnum
from http import HTTPStatus
from pathlib import Path

from PIL import Image
from PIL import ImageChops
from poltergeist_core.services import ServiceError
from poltergeist_core.utilities import logging

from web.icons import frames
from web.icons import palette
from web.icons import poses
from web.icons.frames import IconKind
from web.icons.frames import Layer
from web.icons.frames import Tint
from web.icons.palette import RGB
from web.icons.poses import PartPose
from web.icons.sheet import SpriteSheet
from web.icons.sheet import load_sheet

logger = logging.get_logger(__name__)

_SHEETS_KEPT = 64
_ICON_ID_MAX = 999
# Animation positions are in points at 1x; the texture qualities scale them.
_POINT_SCALE = {"uhd": 4, "hd": 2, "sd": 1}
_ANIMATED_CANVAS = 4.0


class IconError(ServiceError, StrEnum):
    UNKNOWN_KIND = "unknown_kind"
    UNKNOWN_ICON = "unknown_icon"
    INVALID_COLOUR = "invalid_colour"

    def service(self) -> str:
        return "icons"

    def status_code(self) -> int:
        return HTTPStatus.NOT_FOUND


@dataclass(frozen=True, slots=True)
class IconRequest:
    kind: IconKind
    icon_id: int
    colour1: int
    colour2: int
    colour3: int
    glow: bool


@dataclass(frozen=True, slots=True)
class _Tints:
    primary: RGB
    secondary: RGB
    glow: RGB | None

    def resolve(self, tint: Tint) -> RGB | None:
        match tint:
            case Tint.PRIMARY:
                return self.primary
            case Tint.SECONDARY:
                return self.secondary
            case Tint.GLOW:
                return self.glow
            case Tint.WHITE:
                return palette.white()


def _tinted(sprite: Image.Image, colour: RGB) -> Image.Image:
    """The sheets are greyscale with alpha; multiplying paints them."""

    return ImageChops.multiply(sprite, Image.new("RGBA", sprite.size, (*colour, 255)))


def _tints(request: IconRequest) -> _Tints | None:
    primary = palette.rgb(request.colour1)
    secondary = palette.rgb(request.colour2)

    if primary is None or secondary is None:
        return None

    if request.colour3 >= 0 and palette.rgb(request.colour3) is None:
        return None

    glow = None

    if palette.glow_visible(request.colour2, request.glow):
        glow = palette.rgb(
            palette.glow_colour(request.colour1, request.colour2, request.colour3)
        )

    return _Tints(primary=primary, secondary=secondary, glow=glow)


def _compose(
    sheet: SpriteSheet, layers: list[Layer], tints: _Tints
) -> Image.Image | None:
    """Layers share one untrimmed canvas size, so they stack in place."""

    canvas: Image.Image | None = None

    for layer in layers:
        sprite = sheet.crop(layer.name)

        if sprite is None:
            if layer.required:
                return None

            continue

        colour = tints.resolve(layer.tint)

        if colour is None:
            continue

        painted = _tinted(sprite, colour)

        if canvas is None:
            canvas = Image.new("RGBA", painted.size)

        if canvas.size != painted.size:
            grown = Image.new(
                "RGBA",
                (max(canvas.width, painted.width), max(canvas.height, painted.height)),
            )
            grown.alpha_composite(
                canvas,
                (
                    (grown.width - canvas.width) // 2,
                    (grown.height - canvas.height) // 2,
                ),
            )
            canvas = grown

        canvas.alpha_composite(
            painted,
            (
                (canvas.width - painted.width) // 2,
                (canvas.height - painted.height) // 2,
            ),
        )

    return canvas


def _place_part(
    canvas: Image.Image, part: Image.Image, pose: PartPose, scale: int
) -> None:
    if pose.flipped_x:
        part = part.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    if pose.flipped_y:
        part = part.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    if pose.scale_x != 1.0 or pose.scale_y != 1.0:
        part = part.resize(
            (
                max(int(part.width * abs(pose.scale_x)), 1),
                max(int(part.height * abs(pose.scale_y)), 1),
            )
        )

    if pose.rotation:
        # Cocos rotates clockwise for positive angles; Pillow the other way.
        part = part.rotate(
            -pose.rotation, expand=True, resample=Image.Resampling.BICUBIC
        )

    centre_x = canvas.width / 2 + pose.x * scale
    centre_y = canvas.height / 2 - pose.y * scale
    canvas.alpha_composite(
        part, (int(centre_x - part.width / 2), int(centre_y - part.height / 2))
    )


class IconRenderer:
    """Reads the game's per-icon atlases lazily and keeps the recent ones."""

    __slots__ = ("_assets", "_poses", "_quality", "_scale", "_sheets")

    def __init__(self, assets: Path, quality: str) -> None:
        self._assets = assets
        self._quality = quality
        self._scale = _POINT_SCALE.get(quality, 1)
        self._sheets: OrderedDict[str, SpriteSheet | None] = OrderedDict()
        self._poses = {
            IconKind.ROBOT: poses.load_poses(
                assets / "Robot_AnimDesc.plist", IconKind.ROBOT
            ),
            IconKind.SPIDER: poses.load_poses(
                assets / "Spider_AnimDesc.plist", IconKind.SPIDER
            ),
        }

    def supports(self, kind: IconKind) -> bool:
        """Robots and spiders need their animation descriptions to be posed."""

        return not frames.is_animated(kind) or self._poses[kind] is not None

    def _sheet(self, name: str) -> SpriteSheet | None:
        if name in self._sheets:
            self._sheets.move_to_end(name)

            return self._sheets[name]

        folder = self._assets / "icons"
        sheet = load_sheet(
            folder / f"{name}-{self._quality}.png",
            folder / f"{name}-{self._quality}.plist",
        )
        self._sheets[name] = sheet

        while len(self._sheets) > _SHEETS_KEPT:
            self._sheets.popitem(last=False)

        return sheet

    def _render_simple(
        self, request: IconRequest, sheet: SpriteSheet, tints: _Tints
    ) -> Image.Image | None:
        return _compose(sheet, frames.layers(request.kind, request.icon_id), tints)

    def _render_animated(
        self, request: IconRequest, sheet: SpriteSheet, tints: _Tints
    ) -> Image.Image | None:
        part_poses = self._poses[request.kind]

        if part_poses is None:
            return None

        parts = []

        for pose in part_poses:
            layers = frames.part_layers(request.kind, request.icon_id, pose.part)
            # Glow is drawn beneath every limb, so it is split off and placed first.
            glow = _compose(sheet, [layers[0]], tints)
            body = _compose(sheet, layers[1:], tints)

            if body is None:
                return None

            parts.append((pose, glow, body))

        largest = max(max(body.width, body.height) for _, _, body in parts)
        side = int(largest * _ANIMATED_CANVAS)
        canvas = Image.new("RGBA", (side, side))

        for pose, glow, _ in parts:
            if glow is not None:
                _place_part(canvas, glow, pose, self._scale)

        for pose, _, body in parts:
            _place_part(canvas, body, pose, self._scale)

        return canvas.crop(canvas.getbbox() or (0, 0, side, side))

    def render(self, request: IconRequest) -> IconError.OnSuccess[bytes]:
        if not 1 <= request.icon_id <= _ICON_ID_MAX:
            return IconError.UNKNOWN_ICON

        tints = _tints(request)

        if tints is None:
            return IconError.INVALID_COLOUR

        if not self.supports(request.kind):
            return IconError.UNKNOWN_KIND

        sheet = self._sheet(frames.sheet_name(request.kind, request.icon_id))

        if sheet is None:
            return IconError.UNKNOWN_ICON

        if frames.is_animated(request.kind):
            image = self._render_animated(request, sheet, tints)
        else:
            image = self._render_simple(request, sheet, tints)

        if image is None:
            return IconError.UNKNOWN_ICON

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")

        return buffer.getvalue()


def default() -> IconRenderer:
    # Local import keeps this module importable without configuration.
    from web import settings

    renderer = IconRenderer(Path(settings.WEB_ASSETS_PATH), settings.WEB_ICON_QUALITY)
    logger.info(
        "Icon renderer ready.",
        extra={
            "assets": settings.WEB_ASSETS_PATH,
            "quality": settings.WEB_ICON_QUALITY,
            "robots": renderer.supports(IconKind.ROBOT),
            "spiders": renderer.supports(IconKind.SPIDER),
        },
    )

    return renderer
