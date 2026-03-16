import pandas as pd

from api.services.data_normalization_service import (
    POSITION_MAPPING,
    DataNormalizationService,
)
from api.services.ranking_snapshot_service import RankingSnapshotService
from core.players import create_player


class PlayerRankingService:
    """Build ranked player results from normalized stats records.

    This service coordinates data normalization, position remapping, player
    model creation, points calculation, rank metadata enrichment, and
    persistence of the latest rankings snapshot.
    """

    @staticmethod
    def get_player_rankings():
        """Return the current player rankings with computed rank metadata.

        The service normalizes raw competition data into player records, maps
        source position labels to the domain model values expected by
        `create_player`, calculates each player's points, sorts players by
        score, adds `rank`, `previous_rank`, and `rank_change`, and saves the
        resulting rankings snapshot for future comparisons.

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

        # Convert to DataFrame to add rank and rank_change columns
        player_points_df = pd.DataFrame(player_points)
        player_points = DataNormalizationService.add_rank_change(player_points_df)

        RankingSnapshotService.create_snapshot(player_points)
        return player_points
