import logging
from typing import cast

import cloudscraper
from django.db import OperationalError, ProgrammingError
from django.db.models import Manager
from django.db.transaction import atomic
from django.utils import timezone

from api.models import ExternalPlayerStat, ExternalStatsBatch, StatsSource
from api.selectors.stats_selectors import (
    SUPPORTED_STATS_SOURCES,
    get_latest_stats_batches,
)

URL = "https://1xbet.whoscored.com/statisticsfeed/1/getplayerstatistics"
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


def to_int(value) -> int | None:
    """Convert external numeric values to integers when possible."""

    if value is None or value == "":
            return None
    return int(float(value))

def to_float(value) -> float | None:
    """Convert external numeric values to floats when possible."""
    if value is None or value == "":
            return None
    return float(value)

def get_first_int(payload: list[dict], key: str) -> int | None:
    """Return the first integer-like value for a payload field."""

    if not payload:
        return None
    return to_int(payload[0].get(key))

def get_first_str(payload: list[dict], key: str) -> str:
    """Return the first string value for a payload field."""

    if not payload:
        return ""
    return str(payload[0].get(key) or "")

class ExternalStatsService:
    """Fetch and persist external player stats as raw JSON and rows."""

    @staticmethod
    def _batch_manager() -> Manager:
        """Return the default manager for stats batches."""

        return cast(Manager, ExternalStatsBatch._default_manager)

    @staticmethod
    def _player_stat_manager() -> Manager:
        """Return the default manager for normalized player stats."""

        return cast(Manager, ExternalPlayerStat._default_manager)

    @staticmethod
    def sync_if_stale() -> list[ExternalStatsBatch]:
        """Fetch stats only when today's data has not already been stored."""

        if not ExternalStatsService.should_fetch_today():
            logger.info(
                "Skipping external stats fetch because today's data is already stored"
            )
            return []

        logger.info("Fetching external stats because stored data is stale or missing")
        return ExternalStatsService.sync_all_sources()

    @staticmethod
    def should_fetch_today() -> bool:
        """Return whether external stats should be fetched for today."""

        try:
            latest_batches = get_latest_stats_batches()
        except (OperationalError, ProgrammingError):
            logger.debug(
                "Skipping external stats freshness check before database is ready"
            )
            return False
        except Exception:
            logger.exception("Unexpected error while checking external stats freshness")
            return False

        if len(latest_batches) < len(SUPPORTED_STATS_SOURCES):
            return True

        today = timezone.localdate()
        for batch in latest_batches:
            if timezone.localdate(batch.fetched_at) != today:
                return True

        return False

    @staticmethod
    def fetch_and_store_source(source: str) -> ExternalStatsBatch:
        """Fetch one source payload and persist both raw and normalized rows."""

        payload = ExternalStatsService._fetch_source_payload(source)
        with atomic():
            return ExternalStatsService._store_source_payload(source, payload)

    @staticmethod
    def sync_all_sources() -> list[ExternalStatsBatch]:
        """Fetch all sources, then store them atomically as one unit."""

        fetched_payloads = [
            (str(source), ExternalStatsService._fetch_source_payload(str(source)))
            for source in SUPPORTED_STATS_SOURCES
        ]

        with atomic():
            return [
                ExternalStatsService._store_source_payload(source, payload)
                for source, payload in fetched_payloads
            ]

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
    def _store_source_payload(source: str, payload: list[dict]) -> ExternalStatsBatch:
        """Store one fetched payload and its normalized player rows."""

        batch = ExternalStatsService._batch_manager().create(
            source=source,
            season_id=get_first_int(payload, "seasonId"),
            competition_name=get_first_str(payload, "tournamentName"),
            request_params=SOURCE_CONFIG[source]["params"],
            raw_payload=payload,
            record_count=len(payload),
        )
        ExternalStatsService._create_normalized_rows(batch=batch, payload=payload)

        logger.info(
            "Stored %s external stats rows for source '%s' in batch %s",
            len(payload),
            source,
            batch.id,
        )
        return batch

    @staticmethod
    def _create_normalized_rows(batch: ExternalStatsBatch, payload: list[dict]) -> None:
        """Persist query-friendly player stats rows for a batch."""

        player_rows_by_id: dict[int, dict] = {}
        for row in payload:
            player_id = to_int(row.get("playerId"))
            if player_id is None:
                continue

            player_rows_by_id[player_id] = row

        player_stats = [
            ExternalPlayerStat(
                batch=batch,
                source=batch.source,
                player_id=player_id,
                name=str(row.get("name") or ""),
                position_text=str(row.get("positionText") or ""),
                team_id=to_int(row.get("teamId")),
                team_name=str(row.get("teamName") or ""),
                goals=to_int(row.get("goal")) or 0,
                assists=to_int(row.get("assistTotal")) or 0,
                yellow_cards=to_int(row.get("yellowCard")) or 0,
                red_cards=to_int(row.get("redCard")) or 0,
                man_of_the_match=to_int(row.get("manOfTheMatch"))
                or 0,
                appearances=to_int(row.get("apps")) or 0,
                rating=to_float(row.get("rating")) or 0.0,
                raw_row=row,
            )
            for player_id, row in player_rows_by_id.items()
        ]

        ExternalStatsService._player_stat_manager().bulk_create(player_stats)