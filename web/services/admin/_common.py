from collections.abc import Awaitable
from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import field
from enum import StrEnum

from poltergeist_core.services import ServiceError
from poltergeist_core.services import is_error

from web.errors import WebError

PAGE_SIZE = 50
_REASONS_SHOWN = 3


@dataclass(frozen=True, slots=True)
class BulkOutcome:
    """What happened to each selected row; refusals are counted by reason."""

    verb: str
    done: int
    total: int
    refusals: dict[str, int] = field(default_factory=dict)

    def describe(self) -> str:
        text = f"{self.verb} {self.done} of {self.total}."

        if not self.refusals:
            return text

        ordered = sorted(self.refusals.items(), key=lambda item: -item[1])
        reasons = ", ".join(name for name, _ in ordered[:_REASONS_SHOWN])

        if len(ordered) > _REASONS_SHOWN:
            reasons += ", …"

        refused = sum(self.refusals.values())

        return f"{text} {refused} refused: {reasons}."


def member[E: StrEnum](kind: type[E], text: str) -> E | None:
    """A select's "any" option posts an empty value, which no enum holds."""

    return kind(text) if text in kind else None


def selection(ids: Sequence[int] | None) -> WebError.OnSuccess[list[int]]:
    if not ids:
        return WebError.NOTHING_SELECTED

    return list(dict.fromkeys(ids))


async def run_bulk[T](
    ids: Sequence[int],
    action: Callable[[int], Awaitable[ServiceError.OnSuccess[T]]],
    *,
    verb: str,
) -> BulkOutcome:
    """Runs the action per id inside the caller's transaction. A refusal is a
    value, so the rows that succeeded still commit."""

    refusals: dict[str, int] = {}
    done = 0

    for target in ids:
        result = await action(target)

        if is_error(result):
            name = result.resolve_name()
            refusals[name] = refusals.get(name, 0) + 1
        else:
            done += 1

    return BulkOutcome(verb=verb, done=done, total=len(ids), refusals=refusals)
