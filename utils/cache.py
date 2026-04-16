import contextlib
import time
from django.core.cache import cache

@contextlib.contextmanager
def cache_lock(lock_key: str, timeout: int = 600, wait_timeout: int = 30):
    """Distributed lock using django cache.

    Yields:
        bool: True if lock was acquired, False if it timed out.
    """
    start_time = time.time()
    acquired = False
    while time.time() - start_time < wait_timeout:
        if cache.add(lock_key, "locked", timeout=timeout):
            acquired = True
            break
        time.sleep(0.5)

    yield acquired

    if acquired:
        cache.delete(lock_key)
