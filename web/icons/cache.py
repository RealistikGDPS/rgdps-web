from collections import OrderedDict

from web.icons.renderer import IconRequest


class IconCache:
    """Rendered PNGs, most recently used kept. Per process; the reverse proxy
    and the browser cache in front of it do the heavy lifting."""

    __slots__ = ("_entries", "_size")

    def __init__(self, size: int) -> None:
        self._entries: OrderedDict[IconRequest, bytes] = OrderedDict()
        self._size = size

    def get(self, request: IconRequest) -> bytes | None:
        data = self._entries.get(request)

        if data is not None:
            self._entries.move_to_end(request)

        return data

    def put(self, request: IconRequest, data: bytes) -> None:
        self._entries[request] = data
        self._entries.move_to_end(request)

        while len(self._entries) > self._size:
            self._entries.popitem(last=False)
