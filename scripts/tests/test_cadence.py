from datetime import UTC, datetime, timedelta

from scripts.stats_pipeline.cadence import get_next_fetch_day, should_fetch_now


def test_should_fetch_now_true_when_no_manifest():
    assert should_fetch_now(None, datetime.now(UTC), 2) is True


def test_should_fetch_now_false_when_recently_generated():
    now = datetime.now(UTC)
    manifest = {"generated_at": (now - timedelta(days=1)).isoformat()}
    assert should_fetch_now(manifest, now, 2) is False


def test_should_fetch_now_true_at_interval_boundary():
    now = datetime.now(UTC)
    manifest = {"generated_at": (now - timedelta(days=2)).isoformat()}
    assert should_fetch_now(manifest, now, 2) is True


def test_should_fetch_now_true_past_interval():
    now = datetime.now(UTC)
    manifest = {"generated_at": (now - timedelta(days=3)).isoformat()}
    assert should_fetch_now(manifest, now, 2) is True


def test_should_fetch_now_fails_open_on_missing_generated_at():
    assert should_fetch_now({}, datetime.now(UTC), 2) is True


def test_should_fetch_now_fails_open_on_malformed_generated_at():
    manifest = {"generated_at": "not-a-date"}
    assert should_fetch_now(manifest, datetime.now(UTC), 2) is True


def test_get_next_fetch_day():
    dt = datetime(2026, 1, 1, tzinfo=UTC)
    assert get_next_fetch_day(dt, 2) == datetime(2026, 1, 3, tzinfo=UTC)
