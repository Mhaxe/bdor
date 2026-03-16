from django.http import HttpResponse
from django.views import View
from django.views.generic import TemplateView


class IndexView(TemplateView):
    """
    Serves the main index.html file of the React application.
    This view acts as the entry point for the React SPA.
    """

    template_name = "index.html"


class TestPlayersView(View):
    """Test view to display player points calculations"""

    def get(self, request):
        # get some player data
        from .format_data import load_data
        from .players import create_player

        players_df = load_data("core/csv/completeplayers.csv")
        columns_of_interest = [
            "name",
            "goal",
            "assistTotal",
            "positionText",
            "yellowCard",
            "redCard",
        ]

        convert_columns_to = {
            "name": "name",
            "goal": "goals",
            "assistTotal": "assists",
            "positionText": "position",
            "yellowCard": "yellow_cards",
            "redCard": "red_cards",
        }

        # Map CSV positions to expected player positions
        position_mapping = {
            "Forward": "striker",
            "Midfielder": "midfielder",
            "Defender": "defender",
            "Goalkeeper": "keeper",
        }

        players_df = players_df[columns_of_interest]
        players_df = players_df.rename(columns=convert_columns_to)  # type: ignore
        players_records = players_df.to_dict(orient="records")

        # Create player instances and calculate points
        player_points = []
        for record in players_records:
            try:
                # Map position from CSV format to expected format
                csv_position = record.get("position")
                record["position"] = position_mapping.get(csv_position, csv_position)  # type: ignore

                player = create_player(record)
                player_points.append(
                    {
                        "name": record.get("name"),
                        "position": record.get("position"),
                        "points": player.get_points(),
                    }
                )
            except Exception as e:
                print(f"Error creating player from record {record}: {e}")
        player_points = player_points[:100]
        player_points.sort(key=lambda x: x["points"], reverse=True)
        # Build HTML output
        output = "<h1>Player Points</h1><ol>"
        for player_info in player_points:
            output += f"<li>{player_info['name']} ({player_info['position']}): {player_info['points']} points</li>"
        output += "</ol>"

        return HttpResponse(output.encode(), content_type="text/html")
