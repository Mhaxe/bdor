from django.utils import timezone

from api.models import Player
from api.services.data_normalization_service import (
    POSITION_MAPPING,
    DataNormalizationService,
)
from core.players import create_player


class PlayerRankingService:
    """Build ranked player results from normalized stats records.

    This service coordinates data normalization, position remapping, player
    model creation, points calculation, and latest rank persistence.
    """

    @staticmethod
    def get_player_rankings():
        """Return the current player rankings with computed rank metadata.

        The service normalizes raw competition data into player records, maps
        source position labels to the domain model values expected by
        `create_player`, calculates each player's points, sorts players by
        score, and adds `rank`, `previous_rank`, and `rank_change`.

        Returns:
            list[dict]: Ranking records enriched with player stats, points,
            rank, previous rank, and rank change information.
        """
        players_records = DataNormalizationService.normalize_data()
        if not players_records:
            return []

        # Create player instances and calculate points
        player_points = []
        for record in players_records:
            try:
                # Map position from CSV format to expected format
                csv_position = record.get("position")
                record["position"] = POSITION_MAPPING.get(
                    csv_position,  # type: ignore
                    csv_position,  # type: ignore
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
                    }
                )
            except Exception as e:
                print(f"Error creating player from record {record}: {e}")

        # player_points = player_points[:100]
        player_points.sort(key=lambda x: x["points"], reverse=True)

        for index, player in enumerate(player_points):
            current_rank = index + 1
            previous_rank = player.get("previous_rank")
            player["rank"] = current_rank
            player["rank_change"] = DataNormalizationService.calculate_rank_change(
                current_rank, previous_rank
            )

        PlayerRankingService._update_player_ranks(player_points)
        return player_points

    @staticmethod
    def _update_player_ranks(rankings: list[dict]) -> None:
        """Persist latest rank values to Player rows."""

        if not rankings:
            return

        player_ids = [int(ranking["player_id"]) for ranking in rankings]
        players_by_id = {
            player.player_id: player
            for player in Player.objects.filter(player_id__in=player_ids)
        }

        now = timezone.now()
        players_to_update: list[Player] = []
        for ranking in rankings:
            player = players_by_id.get(int(ranking["player_id"]))
            if player is None:
                continue

            player.previous_rank = ranking.get("previous_rank")
            player.rank = ranking["rank"]
            player.updated_at = now
            players_to_update.append(player)

        if players_to_update:
            Player.objects.bulk_update(
                players_to_update,
                ["previous_rank", "rank", "updated_at"],
            )
