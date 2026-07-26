"""Decide whether a fetch is due, mirroring the deleted
ExternalStatsService.should_fetch_today()/get_next_fetch_day() (roughly a
2-day cadence), but gated on S3's summary/latest_manifest.json instead of a
database row - since cron fires far more often than the cadence itself
(hourly), most invocations should just check this and exit immediately.
"""

from datetime import datetime, timedelta


def get_next_fetch_day(dt: datetime, interval_days: int) -> datetime:
    return dt + timedelta(days=interval_days)


def should_fetch_now(manifest: dict | None, now: datetime, interval_days: int) -> bool:
    """manifest is summary/latest_manifest.json's parsed body, or None if it
    doesn't exist yet. Fails open (treats a fetch as due) if generated_at is
    missing or unparseable, rather than crash-looping on a corrupt manifest.
    """
    if manifest is None:
        return True

    generated_at_raw = manifest.get("generated_at")
    if not generated_at_raw:
        return True

    try:
        generated_at = datetime.fromisoformat(generated_at_raw)
    except (TypeError, ValueError):
        return True

    return get_next_fetch_day(generated_at, interval_days) <= now
