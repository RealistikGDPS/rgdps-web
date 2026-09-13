from collections.abc import Sequence

_SPARK_WIDTH = 120
_SPARK_HEIGHT = 32
_CHART_WIDTH = 320
_CHART_HEIGHT = 120


def _points(
    values: Sequence[int], width: int, height: int
) -> list[tuple[float, float]]:
    """Scales a series into SVG space, leaving a hairline of room so the
    stroke at the peak is not clipped."""

    if not values:
        return []

    peak = max(max(values), 1)
    step = width / max(len(values) - 1, 1)
    scale = (height - 2) / peak

    return [
        (round(index * step, 1), round(height - 1 - value * scale, 1))
        for index, value in enumerate(values)
    ]


def spark_points(
    values: Sequence[int], width: int = _SPARK_WIDTH, height: int = _SPARK_HEIGHT
) -> str:
    return " ".join(f"{x},{y}" for x, y in _points(values, width, height))


def line_path(
    values: Sequence[int], width: int = _CHART_WIDTH, height: int = _CHART_HEIGHT
) -> str:
    points = _points(values, width, height)

    if not points:
        return ""

    return "M" + " L".join(f"{x},{y}" for x, y in points)


def area_path(
    values: Sequence[int], width: int = _CHART_WIDTH, height: int = _CHART_HEIGHT
) -> str:
    points = _points(values, width, height)

    if not points:
        return ""

    first_x = points[0][0]
    last_x = points[-1][0]
    line = " L".join(f"{x},{y}" for x, y in points)

    return f"M{first_x},{height} L{line} L{last_x},{height} Z"
