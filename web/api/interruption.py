from fastapi import Response


# The name is fixed by docs/fastapi.md, hence the naming suppression.
class ServiceInterruptionException(Exception):  # noqa: N818
    """The one sanctioned exception: FastAPI's contract for short-circuiting a
    request from a dependency or helper is an exception handled by a registered
    handler. It carries the finished response."""

    def __init__(self, response: Response) -> None:
        self.response = response
