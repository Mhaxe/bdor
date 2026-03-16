import pandas as pd
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.players import create_player
from utils.stats import load_europa_stats, load_league_stats, load_ucl_stats


class Rankings(APIView):
    """API view that returns player points calculations as JSON"""

    def get(self, request):
        try:
            domestic_league_df = load_league_stats()
            ucl_df = load_ucl_stats()
            europa_df = load_europa_stats()

            columns_to_sum = [
                "goals",
                "assists",
                "yellow_cards",
                "red_cards",
                "man_of_the_match",
                "appearances",
            ]

            columns_of_interest = [
                "player_id",
                "name",
                "goals",
                "assists",
                "position",
                "yellow_cards",
                "red_cards",
                "man_of_the_match",
                "team_name",
                "appearances",
                "rating",
            ]

            convert_columns_to = {
                "playerId": "player_id",
                "goal": "goals",
                "assistTotal": "assists",
                "positionText": "position",
                "yellowCard": "yellow_cards",
                "redCard": "red_cards",
                "manOfTheMatch": "man_of_the_match",
                "teamName": "team_name",
                "apps": "appearances",
            }

            # Map CSV positions to expected player positions
            position_mapping = {
                "Forward": "forward",
                "Midfielder": "midfielder",
                "Defender": "defender",
                "Goalkeeper": "keeper",
            }

            # Rename columns in both dataframes first
            domestic_league_df = domestic_league_df.rename(columns=convert_columns_to)  # type: ignore
            ucl_df = ucl_df.rename(columns=convert_columns_to)  # type: ignore
            europa_df = europa_df.rename(columns=convert_columns_to)  # type: ignore

            # Select columns of interest from both dataframes, only if they exist
            domestic_cols = [
                col for col in columns_of_interest if col in domestic_league_df.columns
            ]
            ucl_cols = [col for col in columns_of_interest if col in ucl_df.columns]
            europa_cols = [
                col for col in columns_of_interest if col in europa_df.columns
            ]

            domestic_league_df = domestic_league_df[domestic_cols]
            ucl_df = ucl_df[ucl_cols]
            europa_df = europa_df[europa_cols]

            # Combine both dataframes
            combined_df = pd.concat(
                [domestic_league_df, ucl_df, europa_df], ignore_index=False
            )

            # Aggregate by player_id, summing specified columns and taking first value for others
            combined_df = combined_df.groupby("player_id", as_index=False).agg(
                {
                    col: "sum" if col in columns_to_sum else "first"
                    for col in columns_of_interest
                }
            )

            # Fill missing rating values with 0
            combined_df["rating"] = combined_df["rating"].fillna(0)  # type: ignore

            players_records = combined_df.to_dict(orient="records")  # type: ignore

            # Create player instances and calculate points
            player_points = []
            for record in players_records:
                try:
                    # Map position from CSV format to expected format
                    csv_position = record.get("position")
                    record["position"] = position_mapping.get(
                        csv_position,  # type: ignore
                        csv_position,  # type: ignore
                    )

                    player = create_player(record)
                    player_points.append(
                        {
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

            # Add rank to each player
            for index, player in enumerate(player_points, start=1):
                player["rank"] = index

            return Response(
                {
                    "success": True,
                    "total_players": len(player_points),
                    "players": player_points,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            import traceback

            print(f"Error: {e}")
            print(traceback.format_exc())
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
