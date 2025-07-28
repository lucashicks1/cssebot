"""Collection Utils."""

from abc import ABC
from collections.abc import Awaitable, Callable
from time import time

DEFAULT_CACHE_TTL = 300


class _BaseCache[T, S](ABC):
    """Abstract base class for cache."""

    _ttl: int
    _cache: dict[T, tuple[float, S | None]]

    def __init__(self, ttl: int) -> None:
        """Abstract cache."""
        self._ttl = ttl
        self._cache = {}

    def _is_valid(self, timestamp: float) -> bool:
        return (time() - timestamp) < self._ttl

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()

    def set(self, key: T, value: S) -> None:
        """Set an item in the cache."""
        self._cache[key] = (time(), value)

    def remove(self, key: T) -> bool:
        """Remove an item from the cache."""
        found = self._cache.pop(key, None)
        return found is not None

    def __contains__(self, key: T) -> bool:
        cached = self._cache.get(key)
        return cached is not None and self._is_valid(cached[0])


class SyncCache[T, S](_BaseCache[T, S]):
    """Synchronous cache."""

    _fetch_callback: Callable[[T], S | None]

    def __init__(self, fetch_callback: Callable[[T], S | None], ttl: int = DEFAULT_CACHE_TTL) -> None:
        """Construct a synchronous cache.

        Args:
            fetch_callback (Callable[[T], S  |  None]): callable to fetch data
            ttl (int, optional): basic time to live (in seconds). Defaults to DEFAULT_CACHE_TTL.
        """
        super().__init__(ttl)
        self._fetch_callback = fetch_callback

    def get(self, key: T) -> S | None:
        """Get something from the cache."""
        cached = self._cache.get(key)
        if cached and self._is_valid(cached[0]):
            return cached[1]

        if key in self._cache:
            return None

        result = self._fetch_callback(key)
        self._cache[key] = (time(), result)
        return result


class AsyncCache[T, S](_BaseCache[T, S]):
    """Asynchronous cache."""

    _fetch_callback: Callable[[T], Awaitable[S | None]]

    def __init__(self, fetch_callback: Callable[[T], Awaitable[S | None]], ttl: int = DEFAULT_CACHE_TTL) -> None:
        """Construct a asynchronous cache.

        Args:
            fetch_callback (Callable[[T], Awaitable[S  |  None]]): async callable to fetch data
            ttl (int, optional): basic time to live (in seconds). Defaults to DEFAULT_CACHE_TTL.
        """
        super().__init__(ttl)
        self._fetch_callback = fetch_callback

    async def get(self, key: T) -> S | None:
        """Get something from the cache."""
        cached = self._cache.get(key)
        if cached and self._is_valid(cached[0]):
            return cached[1]

        if key in self._cache:
            return None

        result = await self._fetch_callback(key)
        self._cache[key] = (time(), result)
        return result
