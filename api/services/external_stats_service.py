import logging
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import cloudscraper
from django.db import OperationalError, ProgrammingError
from django.db.transaction import atomic
from django.utils import timezone
from django.conf import settings

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
            "page": "1",
            "numberOfPlayersToPick": "2300",
        }
    },
    str(StatsSource.UCL): {
        "params": {
            "category": "summary",
            "subcategory": "all",
            "statsAccumulationType": "0",
            "isCurrent": "true",
            "stageId": "24796",
            "tournamentOptions": "12",
            "sortBy": "Rating",
            "field": "Overall",
            "isMinApp": "false",
            "page": "1",
            "numberOfPlayersToPick": "774",
        }
    },
    str(StatsSource.EUROPA): {
        "params": {
            "category": "summary",
            "subcategory": "all",
            "statsAccumulationType": "0",
            "isCurrent": "true",
            "stageId": "24798",
            "tournamentOptions": "30",
            "sortBy": "Rating",
            "field": "Overall",
            "isMinApp": "false",
            "page": "1",
            "numberOfPlayersToPick": "789",
        }
    },
}

SUPPORTED_STATS_SOURCES = list(StatsSource.values)

class ExternalStatsService:
    """Fetch external stats and upsert one stable combined player row per player."""

    @staticmethod
    def get_next_thursday(dt):
        """Calculate the next Thursday always in the future."""
        # Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
        days_ahead = 7 - (dt.weekday() - 3) % 7
        return dt + timedelta(days=days_ahead)

    @staticmethod
    def sync_if_stale() -> list[dict]:
        """Fetch stats only when today's data has not already been stored.

        When fetching is not required, this method still returns the latest
        computed rankings from the database so callers do not need to invoke
        `PlayerRankingService.get_player_rankings()`.
        """

        if not ExternalStatsService.should_fetch_today():
            logger.info(
                "Skipping external stats fetch"
            )
            return PlayerRankingService.get_player_rankings()

        logger.info("Fetching external stats")
        return ExternalStatsService.fetch_external_stats()

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
    def _fetch_source_payload(source: str) -> list[dict]:
        """Fetch one source payload from the external API."""

        config = SOURCE_CONFIG[source]
        scraper = cloudscraper.create_scraper()
        logger.info("Fetching external stats for source '%s'", source)
        response = scraper.get(URL, params=config["params"], headers={})
        response.raise_for_status()
        return response.json().get("playerTableStats", [])

    @staticmethod
    def update_stats():
        scraper = cloudscraper.create_scraper()
        response = scraper.get(settings.UPDATE_URL)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def fetch_external_stats() -> list[dict]:
        """Fetch all sources in parallel, compute rankings, and persist aggregated players.

        Returns:
            list[dict]: The computed player ranking records.
        """

        # Fetch each source payload concurrently to reduce total latency.
        fetched_payloads: list[tuple[str, list[dict]]] = []
        with ThreadPoolExecutor(max_workers=len(SUPPORTED_STATS_SOURCES)) as executor:
            future_to_source = {
                executor.submit(ExternalStatsService._fetch_source_payload, str(source)): str(source)
                for source in SUPPORTED_STATS_SOURCES
            }

            for future in as_completed(future_to_source):
                source = future_to_source[future]
                fetched_payloads.append((source, future.result()))

        # Maintain deterministic ordering across runs (matching SUPPORTED_STATS_SOURCES).
        fetched_payloads.sort(key=lambda item: SUPPORTED_STATS_SOURCES.index(item[0]))

        normalized_records = DataNormalizationService.normalize_payloads(fetched_payloads)

        # Compute rankings and persist players/ranks in a single place.
        with atomic():
            rankings = PlayerRankingService.get_player_rankings(
                player_records=normalized_records, persist=True
            )

            # Update fetch record for next time
            fetch_record = FetchRecord.objects.first()
            now = timezone.now()
            if fetch_record:
                fetch_record.last_fetch_at = now
                fetch_record.fetch_next_at = ExternalStatsService.get_next_thursday(now)
                fetch_record.save()
            else:
                FetchRecord.objects.create(
                    fetch_next_at=ExternalStatsService.get_next_thursday(now),
                    last_fetch_at=now,
                )
        return rankings
