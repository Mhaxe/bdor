from django.utils import timezone

from api.models import Player
from api.services.data_normalization_service import (
    POSITION_MAPPING,
    DataNormalizationService,
)
from core.players import create_player

SQLITE_SAFE_BULK_BATCH_SIZE = 100


class PlayerRankingService:
    """Build ranked player results from normalized stats records.

    This service coordinates data normalization, position remapping, player
    model creation, points calculation, and latest rank persistence.
    """

    @staticmethod
    def get_player_rankings(
        player_records: list[dict] | None = None, *, persist: bool = False
    ) -> list[dict]:
        """Return the current player rankings with computed rank metadata."""
        players_records = (
            player_records
            if player_records is not None
            else DataNormalizationService.normalize_data()
        )
        if not players_records:
            return []

        # Create player instances and calculate points
        player_points = []
        for record in players_records:
            try:
                # Map position to expected format
                position = record.get("position")
                record["position"] = POSITION_MAPPING.get(
                    position,  # type: ignore
                    position,  # type: ignore
                )

                player = create_player(record)
                player_points.append(
                    {
                        "player_id": record.get("player_id"),
                        "name": record.get("name"),
                        "position": record.get("position"),
                        "points": player.get_points(),
                        "goals": player.goals,
                        "assists": player.assists,
                        "team_name": record.get("team_name"),
                        "yellow_cards": player.yellow_cards,
                        "red_cards": player.red_cards,
                        "man_of_the_match": player.man_of_the_match,
                        "rating": player.rating,
                        "appearances": player.appearances,
                        "competitions_count": int(record.get("competitions_count") or 0),
                        "previous_rank": record.get("previous_rank"),
                    }
                )
            except Exception as e:
                print(f"Error creating player from record {record}: {e}")

        player_points.sort(key=lambda x: x["points"], reverse=True)

        for index, player in enumerate(player_points):
            current_rank = index + 1
            previous_rank = player.get("previous_rank")
            player["rank"] = current_rank
            player["rank_change"] = DataNormalizationService.calculate_rank_change(
                current_rank, previous_rank
            )

        if persist:
            PlayerRankingService._update_player_ranks(player_points)

        return player_points

    @staticmethod
    def _update_player_ranks(rankings: list[dict]) -> None:
        """Persist latest rank values to Player rows.

        This method is responsible for ensuring the database contains one
        stable row per player. It will create missing players and update
        existing players with the latest stats and ranking metadata.
        """

        if not rankings:
            return

        player_ids = [int(ranking["player_id"]) for ranking in rankings]
        players_by_id = {
            player.player_id: player
            for player in Player.objects.filter(player_id__in=player_ids)
        }

        now = timezone.now()
        to_create: list[Player] = []
        to_update: list[Player] = []

        for ranking in rankings:
            player_id = int(ranking["player_id"])
            existing = players_by_id.get(player_id)

            player_kwargs = {
                "player_id": player_id,
                "name": str(ranking.get("name") or ""),
                "position_text": str(ranking.get("position") or ""),
                "team_name": str(ranking.get("team_name") or ""),
                "goals": int(ranking.get("goals") or 0),
                "assists": int(ranking.get("assists") or 0),
                "yellow_cards": int(ranking.get("yellow_cards") or 0),
                "red_cards": int(ranking.get("red_cards") or 0),
                "man_of_the_match": int(ranking.get("man_of_the_match") or 0),
                "appearances": int(ranking.get("appearances") or 0),
                "rating": float(ranking.get("rating") or 0.0),
                "competitions_count": int(ranking.get("competitions_count") or 0),
                "rank": ranking.get("rank"),
                "previous_rank": ranking.get("previous_rank"),
                "updated_at": now,
            }

            if existing is None:
                to_create.append(Player(**player_kwargs))
                continue

            existing.name = player_kwargs["name"]
            existing.position_text = player_kwargs["position_text"]
            existing.team_name = player_kwargs["team_name"]
            existing.goals = player_kwargs["goals"]
            existing.assists = player_kwargs["assists"]
            existing.yellow_cards = player_kwargs["yellow_cards"]
            existing.red_cards = player_kwargs["red_cards"]
            existing.man_of_the_match = player_kwargs["man_of_the_match"]
            existing.appearances = player_kwargs["appearances"]
            existing.rating = player_kwargs["rating"]
            existing.competitions_count = player_kwargs["competitions_count"]
            existing.rank = player_kwargs["rank"]
            existing.previous_rank = player_kwargs["previous_rank"]
            existing.updated_at = now
            to_update.append(existing)

        if to_create:
            Player.objects.bulk_create(
                to_create,
                batch_size=SQLITE_SAFE_BULK_BATCH_SIZE,
            )
        if to_update:
            Player.objects.bulk_update(
                to_update,
                [
                    "name",
                    "position_text",
                    "team_name",
                    "goals",
                    "assists",
                    "yellow_cards",
                    "red_cards",
                    "man_of_the_match",
                    "appearances",
                    "rating",
                    "competitions_count",
                    "rank",
                    "previous_rank",
                    "updated_at",
                ],
                batch_size=SQLITE_SAFE_BULK_BATCH_SIZE,
            )
