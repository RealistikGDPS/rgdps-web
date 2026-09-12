from collections.abc import AsyncGenerator
from typing import override

from fastapi import Request
from poltergeist_core.adapters.boomlings import BoomlingsClient
from poltergeist_core.adapters.mysql import ImplementsMySQL
from poltergeist_core.adapters.mysql import MySQLPool
from poltergeist_core.adapters.redis import RedisClient
from poltergeist_core.adapters.storage import ImplementsStorage
from poltergeist_core.services import AbstractContext


class HTTPContext(AbstractContext):
    """Reads: the connection pool is used directly."""

    __slots__ = ("_request",)

    def __init__(self, request: Request) -> None:
        self._request = request

    @property
    @override
    def _mysql(self) -> ImplementsMySQL:
        mysql: MySQLPool = self._request.app.state.mysql

        return mysql

    @property
    @override
    def _redis(self) -> RedisClient:
        redis: RedisClient = self._request.app.state.redis

        return redis

    @property
    @override
    def storage(self) -> ImplementsStorage:
        storage: ImplementsStorage = self._request.app.state.storage

        return storage

    @property
    @override
    def boomlings(self) -> BoomlingsClient:
        boomlings: BoomlingsClient = self._request.app.state.boomlings

        return boomlings


class HTTPTransactionContext(AbstractContext):
    """Writes: one transaction that commits on success and rolls back on
    exception."""

    __slots__ = (
        "_boomlings_client",
        "_redis_client",
        "_storage_backend",
        "_transaction",
    )

    def __init__(
        self,
        transaction: ImplementsMySQL,
        redis: RedisClient,
        storage: ImplementsStorage,
        boomlings: BoomlingsClient,
    ) -> None:
        self._transaction = transaction
        self._redis_client = redis
        self._storage_backend = storage
        self._boomlings_client = boomlings

    @property
    @override
    def _mysql(self) -> ImplementsMySQL:
        return self._transaction

    @property
    @override
    def _redis(self) -> RedisClient:
        return self._redis_client

    @property
    @override
    def storage(self) -> ImplementsStorage:
        return self._storage_backend

    @property
    @override
    def boomlings(self) -> BoomlingsClient:
        return self._boomlings_client


async def transaction_context(
    request: Request,
) -> AsyncGenerator[HTTPTransactionContext]:
    pool: MySQLPool = request.app.state.mysql

    async with pool.transaction() as transaction:
        yield HTTPTransactionContext(
            transaction,
            request.app.state.redis,
            request.app.state.storage,
            request.app.state.boomlings,
        )


def client_ip(request: Request) -> str:
    """Uvicorn already resolves proxy headers when APP_TRUST_PROXY_HEADERS is on."""

    if request.client is None:
        return "0.0.0.0"

    return request.client.host
