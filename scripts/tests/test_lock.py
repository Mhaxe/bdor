import pytest

from scripts.stats_pipeline.lock import LockHeldError, acquire_lock


def test_acquire_lock_succeeds_and_releases(tmp_path):
    lock_path = str(tmp_path / "test.lock")

    with acquire_lock(lock_path):
        pass

    # Released on exit, so acquiring again immediately should succeed.
    with acquire_lock(lock_path):
        pass


def test_acquire_lock_raises_when_already_held(tmp_path):
    lock_path = str(tmp_path / "test.lock")

    with acquire_lock(lock_path), pytest.raises(LockHeldError):
        with acquire_lock(lock_path):
            pass
