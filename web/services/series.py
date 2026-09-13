from dataclasses import dataclass
from datetime import date
from datetime import timedelta

from poltergeist_core.resources import DailyCount


@dataclass(frozen=True, slots=True)
class Chart:
    """A day-by-day series with the gaps filled, ready to draw."""

    title: str
    points: list[DailyCount]
    peak: int
    total: int

    @property
    def values(self) -> list[int]:
        return [point.count for point in self.points]


def fill(series: list[DailyCount], days: int, today: date) -> list[DailyCount]:
    """Every day of the window, ending today, with zeros where nothing happened."""

    counts = {entry.day: entry.count for entry in series}

    return [
        DailyCount(day=day, count=counts.get(day, 0))
        for day in (
            today - timedelta(days=offset) for offset in range(days - 1, -1, -1)
        )
    ]


def chart(title: str, series: list[DailyCount], days: int, today: date) -> Chart:
    points = fill(series, days, today)

    return Chart(
        title=title,
        points=points,
        peak=max((point.count for point in points), default=0),
        total=sum(point.count for point in points),
    )
