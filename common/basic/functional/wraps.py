import contextlib
import functools
import logging
import threading
import time
from typing import Any


def cache_it(timeout: int = 60):  # in seconds
    def wrapper(fn):
        _cache = {}

        @functools.wraps(fn)
        def inner(*args, **kwargs):
            nonlocal _cache
            force_update = kwargs.pop("__force_update_cache_it__", False)
            key_ = str((args, tuple(sorted(kwargs.items()))))
            val, expired_at = _cache.get(key_) or (None, None)

            if force_update or expired_at is None or expired_at < time.time():
                _cache.pop(key_, None)
                val = fn(*args, **kwargs)
                expired_at = time.time() + timeout
                _cache[key_] = (val, expired_at)

            return val

        return inner

    return wrapper


def error_interrupter(logger: logging.Logger, interrupt: bool = False, default: Any = None):
    def wrapper(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Error in {fn}, error: {e}")

                if interrupt:
                    return default
                else:
                    raise e

        return inner

    return wrapper


_TABLE = {}
_TABLE_LOCK = threading.Lock()


@contextlib.contextmanager
def timeout_lock(lock_name: str, timeout: float = 10, raise_if_timeout: bool = False):
    with _TABLE_LOCK:
        lock, counter = _TABLE.get(lock_name) or (threading.Lock(), 0)
        counter += 1
        _TABLE[lock_name] = (lock, counter)

    acquired = False
    try:
        acquired = lock.acquire(timeout=timeout)
        if not acquired and raise_if_timeout:
            raise TimeoutError(f"Acquire lock timeout. lock_name: {lock_name}")

        yield acquired
    finally:
        if acquired:
            lock.release()

        with _TABLE_LOCK:
            lock, counter = _TABLE[lock_name]
            counter -= 1

            if counter == 0:
                _TABLE.pop(lock_name)
            else:
                _TABLE[lock_name] = (lock, counter)
