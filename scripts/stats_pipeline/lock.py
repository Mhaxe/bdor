"""Simple flock-based lock so overlapping cron runs no-op instead of
double-fetching (a full run's jittered network calls can take minutes;
hourly cron could otherwise overlap a slow one).
"""

import fcntl
from contextlib import contextmanager


class LockHeldError(Exception):
    """Another instance of the pipeline script is already running."""


@contextmanager
def acquire_lock(path: str):
    fh = open(path, "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fh.close()
        raise LockHeldError(f"Lock file {path} already held by another run")

    try:
        yield
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()
