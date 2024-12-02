import time
from typing import Any

from fastapi import HTTPException, Request


class TimedCache[K, V](dict):
    def __init__(self, max_size: int, ttl: int):
        super().__init__()

        self._data = dict()
        self._data_times = dict()
        self._max_size = max_size
        self._current_size = 0
        self._ttl = ttl

    def get(self, key: K, default: V | None = None) -> V | None:
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __getitem__(self, key: K) -> V:
        data = self._data[key]
        data_time = self._data_times[key]
        if self._ttl > time.time() - data_time:
            return data

        self._data.pop(key)
        self._data_times.pop(key)

        raise KeyError("Key expired")

    def __setitem__(self, key: K, value: V):
        if self._current_size > self._max_size:
            if key not in self._data.keys():
                oldest_key = sorted(
                    self._data_times.items(), key=lambda obj: obj[1]
                )
                self._data.pop(oldest_key[0])
                self._data_times.pop(oldest_key[0])
            else:
                self._current_size += 1

        self._data[key] = value
        self._data_times[key] = time.time()

    def __getattribute__(self, item: str) -> Any:
        if str(item).startswith("__"):
            return object.__getattribute__(self, item)

        if str(item) in (
            "_data",
            "_data_times",
            "_max_size",
            "_current_size",
            "_ttl",
            "get",
        ):
            return object.__getattribute__(self, item)

        return object.__getattribute__(self, "_data").__getattribute__(item)


class SizedCache[K, V](TimedCache[K, V]):
    def __init__(self, max_size: int):
        super().__init__(max_size=max_size, ttl=0)

        self._data = dict()
        self._data_times = dict()
        self._max_size = max_size
        self._current_size = 0

    def __getitem__(self, key: K) -> V:
        return self._data[key]


def get_request_ip(request: Request) -> str:
    if request.client is not None:
        ip = request.client.host
    elif request.headers.get("x-tauth-ip"):
        ip = request.headers["x-tauth-ip"]
    elif request.headers.get("x-forwarded-for"):
        ip = request.headers["x-forwarded-for"]
    else:
        raise HTTPException(
            500,
            detail=(
                "Client's IP was not found in: request.client.host, "
                "X-Tauth-IP, X-Forwarded-For."
            ),
        )
    return ip
