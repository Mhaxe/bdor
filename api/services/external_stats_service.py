import logging

import cloudscraper
from django.db import OperationalError, ProgrammingError
from django.db.transaction import atomic
from django.utils import timezone

from api.models import Player, StatsSource

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

SUPPORTED_STATS_SOURCES = list(StatsSource.values)


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


class ExternalStatsService:
    """Fetch external stats and upsert one stable combined player row per player."""

    @staticmethod
    def sync_if_stale() -> list[tuple[str, list[dict]]]:
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
            latest_player = Player.objects.order_by("-updated_at", "player_id").first()
        except (OperationalError, ProgrammingError):
            logger.debug(
                "Skipping external stats freshness check before database is ready"
            )
            return False
        except Exception:
            logger.exception("Unexpected error while checking external stats freshness")
            return False

        if latest_player is None:
            return True

        today = timezone.localdate()
        return timezone.localdate(latest_player.updated_at) != today

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
    def _upsert_players_from_payloads(
        fetched_payloads: list[tuple[str, list[dict]]],
    ) -> None:
        """Aggregate source payloads and upsert one stable row per player."""

        players_by_id: dict[int, dict] = {}

        for _, payload in fetched_payloads:
            for row in payload:
                player_id = to_int(row.get("playerId"))
                if player_id is None:
                    continue

                if player_id not in players_by_id:
                    players_by_id[player_id] = {
                        "name": str(row.get("name") or ""),
                        "position_text": str(row.get("positionText") or ""),
                        "team_id": to_int(row.get("teamId")),
                        "team_name": str(row.get("teamName") or ""),
                        "stats": {
                            "goals": 0,
                            "assists": 0,
                            "yellow_cards": 0,
                            "red_cards": 0,
                            "man_of_the_match": 0,
                            "appearances": 0,
                            "rating": 0.0,
                        },
                        "rating_total": 0.0,
                        "rating_count": 0,
                    }

                player = players_by_id[player_id]
                stats = player["stats"]
                stats["goals"] += to_int(row.get("goal")) or 0
                stats["assists"] += to_int(row.get("assistTotal")) or 0
                stats["yellow_cards"] += to_int(row.get("yellowCard")) or 0
                stats["red_cards"] += to_int(row.get("redCard")) or 0
                stats["man_of_the_match"] += to_int(row.get("manOfTheMatch")) or 0
                stats["appearances"] += to_int(row.get("apps")) or 0

                rating = to_float(row.get("rating"))
                if rating is not None:
                    player["rating_total"] += rating
                    player["rating_count"] += 1

                if not player["name"]:
                    player["name"] = str(row.get("name") or "")
                if not player["position_text"]:
                    player["position_text"] = str(row.get("positionText") or "")
                if not player["team_name"]:
                    player["team_name"] = str(row.get("teamName") or "")
                if player["team_id"] is None:
                    player["team_id"] = to_int(row.get("teamId"))

        if not players_by_id:
            return

        now = timezone.now()
        player_ids = list(players_by_id.keys())
        existing_players = {
            player.player_id: player
            for player in Player.objects.filter(player_id__in=player_ids)
        }

        to_create: list[Player] = []
        to_update: list[Player] = []

        for player_id, data in players_by_id.items():
            stats = data["stats"]
            rating_count = data["rating_count"]
            stats["rating"] = (
                round(data["rating_total"] / rating_count, 2) if rating_count else 0.0
            )

            existing = existing_players.get(player_id)
            if existing is None:
                to_create.append(
                    Player(
                        player_id=player_id,
                        name=data["name"],
                        position_text=data["position_text"],
                        team_id=data["team_id"],
                        team_name=data["team_name"],
                        stats=stats,
                        updated_at=now,
                    )
                )
                continue

            existing.name = data["name"]
            existing.position_text = data["position_text"]
            existing.team_id = data["team_id"]
            existing.team_name = data["team_name"]
            existing.stats = stats
            existing.updated_at = now
            to_update.append(existing)

        if to_create:
            Player.objects.bulk_create(to_create)
        if to_update:
            Player.objects.bulk_update(
                to_update,
                ["name", "position_text", "team_id", "team_name", "stats", "updated_at"],
            )

    @staticmethod
    def sync_all_sources() -> list[tuple[str, list[dict]]]:
        """Fetch all sources and upsert aggregated players."""

        fetched_payloads = [
            (str(source), ExternalStatsService._fetch_source_payload(str(source)))
            for source in SUPPORTED_STATS_SOURCES
        ]

        with atomic():
            ExternalStatsService._upsert_players_from_payloads(fetched_payloads)
            return fetched_payloads
