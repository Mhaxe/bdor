import logging
import random
import time
from datetime import timedelta

import cloudscraper
import contextlib
from django.db import OperationalError, ProgrammingError
from django.db.transaction import atomic
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache

from api.models import StatsSource, FetchRecord
from api.services.data_normalization_service import DataNormalizationService
from api.services.player_ranking_service import PlayerRankingService

URL = settings.STATS_URL
logger = logging.getLogger(__name__)

SOURCE_CONFIG: dict[str, dict[str, dict[str, str]]] = {
    str(StatsSource.LEAGUE): {
        "params": {
            "category": "summary",
            "subcategory": "all",
            "statsAccumulationType": "0",
            "isCurrent": "true",
            "tournamentOptions": "2,3,4,5,22",
            "sortBy": "Rating",
            "field": "Overall",
            "isMinApp": "false",
            "numberOfPlayersToPick": "2300",
        }
    },
    str(StatsSource.UCL): {
        "params": {
            "category": "summary",
            "subcategory": "all",
            "statsAccumulationType": "0",
            "isCurrent": "true",
            "stageId": "24797",
            "tournamentOptions": "12",
            "sortBy": "Rating",
            "field": "Overall",
            "isMinApp": "false",
            "numberOfPlayersToPick": "774",
        }
    },
    str(StatsSource.EUROPA): {
        "params": {
            "category": "summary",
            "subcategory": "all",
            "statsAccumulationType": "0",
            "isCurrent": "true",
            "stageId": "24799",
            "tournamentOptions": "30",
            "sortBy": "Rating",
            "field": "Overall",
            "isMinApp": "false",
            "numberOfPlayersToPick": "789",
        }
    },
}


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


SUPPORTED_STATS_SOURCES = list(StatsSource.values)

class ExternalStatsService:
    """Fetch external stats and upsert one stable combined player row per player."""

    @staticmethod
    def get_next_fetch_day(dt):
        return dt + timedelta(days=2)

    @staticmethod
    def update_stats() -> list[dict]:
        """Fetch stats only when today's data has not already been stored.

        Uses a distributed lock and double-checked locking to prevent multiple
        concurrent requests from triggering redundant external API calls.
        """
        
        # First fast check (unlocked)
        if not ExternalStatsService.should_fetch_today():
            logger.info("Skipping external stats fetch (data is fresh)")
            return PlayerRankingService.get_player_rankings()

        # Attempt to acquire a distributed lock
        lock_key = "lock:external_stats_fetch"
        with cache_lock(lock_key, timeout=600, wait_timeout=30) as acquired:
            if not acquired:
                logger.warning(
                    "Timed out waiting for external stats fetch lock. "
                    "Returning existing rankings."
                )
                return PlayerRankingService.get_player_rankings()

            # Second check (locked) - another request might have finished the fetch
            if not ExternalStatsService.should_fetch_today():
                logger.info(
                    "Skipping external stats fetch (fetch completed by another process)"
                )
                return PlayerRankingService.get_player_rankings()

            logger.info("Fetching external stats")
            try:
                player_points = ExternalStatsService.fetch_external_stats()
            except Exception:
                logger.exception("Failed to fetch external stats")
                player_points = PlayerRankingService.get_player_rankings()
            return player_points

    @staticmethod
    def should_fetch_today() -> bool:
        """Return whether external stats should be fetched for today."""

        try:
            fetch_record = FetchRecord.objects.first()
            if fetch_record is None:
                return True
            return fetch_record.fetch_next_at < timezone.now()
        except (OperationalError, ProgrammingError):
            logger.debug(
                "Skipping external stats check before database is ready"
            )
            return False
        except Exception:
            logger.exception("Unexpected error while checking external stats")
            return False

    @staticmethod
    def _fetch_source_payload(source: str, scraper: cloudscraper.CloudScraper | None = None) -> list[dict]:
        """Fetch one source payload from the external API.

        Args:
            source: The identifier for the stat source.
            scraper: Optional scraper session to reuse. If not provided, a new one is created.
        """

        config = SOURCE_CONFIG[source]
        if scraper is None:
            scraper = cloudscraper.create_scraper()

        logger.info("Fetching external stats for source '%s'", source)
        response = scraper.get(URL, params=config["params"], headers={})
        response.raise_for_status()
        return response.json().get("playerTableStats", [])

    @staticmethod
    def fetch_external_stats() -> list[dict]:
        """Fetch all sources sequentially, compute rankings, and persist aggregated players.

        Returns:
            list[dict]: The computed player ranking records.
        """
        
        # Fetch each source payload sequentially with jitter to avoid IP blocking.
        fetched_payloads: list[tuple[str, list[dict]]] = []
        scraper = cloudscraper.create_scraper()
        if not settings.DEBUG:
            for i, source in enumerate(SUPPORTED_STATS_SOURCES):
                # Add a small random delay between requests (except the first one) to mimic human behavior.
                if i > 0:
                    delay = random.uniform(1, 5)
                    logger.debug("Sleeping for %.2f seconds before fetching next source", delay)
                    time.sleep(delay)

            source_str = str(source)
            try:
                data = ExternalStatsService._fetch_source_payload(source_str, scraper=scraper)
                fetched_payloads.append((source_str, data))
            except Exception:
                logger.exception("Failed to fetch external stats for source '%s'", source_str)
                raise
        else:
            import json
            from pathlib import Path
            sample_path = Path(__file__).resolve().parents[2] / "core" / "stats" / "leagues_sample_data.json"
            with sample_path.open(encoding="utf-8") as f:
                data = json.load(f)
            player_stats = data.get("playerTableStats", [])
            fetched_payloads = [(str(StatsSource.LEAGUE), player_stats)]
            logger.info(
                "DEBUG mode: returning stub rankings from leagues_sample_data.json (%d players)",
                len(player_stats),
            )

        # Maintain deterministic ordering across runs (matching SUPPORTED_STATS_SOURCES).
        fetched_payloads.sort(key=lambda item: SUPPORTED_STATS_SOURCES.index(item[0]))

        normalized_records = DataNormalizationService.normalize_payloads(fetched_payloads)

        # Compute rankings and persist players/ranks in a single place.
        with atomic():
            rankings = PlayerRankingService.get_player_rankings(
                player_records=normalized_records, persist=not settings.DEBUG
            )

            # Update fetch record for next time
            fetch_record = FetchRecord.objects.first()
            now = timezone.now()
            if fetch_record:
                fetch_record.last_fetch_at = now
                fetch_record.fetch_next_at = ExternalStatsService.get_next_fetch_day(now)
                fetch_record.save()
            else:
                FetchRecord.objects.create(
                    fetch_next_at=ExternalStatsService.get_next_fetch_day(now),
                    last_fetch_at=now,
                )
        return rankings
