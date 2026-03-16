from api.models import Player

POSITION_MAPPING = {
    "Forward": "forward",
    "Midfielder": "midfielder",
    "Defender": "defender",
    "Goalkeeper": "keeper",
}


class DataNormalizationService:
    """Normalize Player rows into ranking-ready records."""

    @staticmethod
    def normalize_data() -> list[dict]:
        """Load and normalize stored player rows into ranking-ready records."""

        players = Player.objects.all().order_by("player_id")
        normalized: list[dict] = []

        for player in players:
            stats = player.stats or {}
            normalized.append(
                {
                    "player_id": player.player_id,
                    "name": player.name,
                    "position": player.position_text,
                    "goals": int(stats.get("goals") or 0),
                    "assists": int(stats.get("assists") or 0),
                    "yellow_cards": int(stats.get("yellow_cards") or 0),
                    "red_cards": int(stats.get("red_cards") or 0),
                    "man_of_the_match": int(stats.get("man_of_the_match") or 0),
                    "team_name": player.team_name,
                    "appearances": int(stats.get("appearances") or 0),
                    "rating": float(stats.get("rating") or 0.0),
                    "previous_rank": player.rank,
                }
            )

        return normalized

    @staticmethod
    def calculate_rank_change(current_rank, previous_rank):
        """Return rank change state from current and previous ranking."""

        if previous_rank is None:
            return "same"
        if current_rank < previous_rank:
            return "up"
        if current_rank > previous_rank:
            return "down"
        return "same"
