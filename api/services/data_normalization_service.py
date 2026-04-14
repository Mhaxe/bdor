import pandas as pd

from api.models import Player

POSITION_MAPPING = {
    "Forward": "forward",
    "Midfielder": "midfielder",
    "Defender": "defender",
    "Goalkeeper": "keeper",
}


class DataNormalizationService:
    """Normalize Player rows or external stats payloads into ranking-ready records."""

    @staticmethod
    def normalize_data() -> list[dict]:
        """Load and normalize stored player rows into ranking-ready records."""
        # TODO: in development we can use a stub for the normalized data because database might not contain data yet

        players = Player.objects.all().order_by("player_id")
        normalized: list[dict] = []

        for player in players:
            normalized.append(
                {
                    "player_id": player.player_id,
                    "name": player.name,
                    "position": player.position_text,
                    "goals": int(player.goals or 0),
                    "assists": int(player.assists or 0),
                    "yellow_cards": int(player.yellow_cards or 0),
                    "red_cards": int(player.red_cards or 0),
                    "man_of_the_match": int(player.man_of_the_match or 0),
                    "team_name": player.team_name,
                    "appearances": int(player.appearances or 0),
                    "rating": float(player.rating or 0.0),
                    "competitions_count": int(player.competitions_count or 0),
                    "previous_rank": player.previous_rank,
                }
            )

        return normalized

    @staticmethod
    def normalize_payloads(fetched_payloads: list[tuple[str, list[dict]]]) -> list[dict]:
        """Normalize external payloads into ranking-ready records.

        This method aggregates multiple source payloads into one record per player
        and enriches the record with the player's most recently stored previous
        rank (when available).
        """

        # Flatten all payloads into a single table
        rows: list[dict] = []
        for _, payload in fetched_payloads:
            rows.extend(payload or [])

        if not rows:
            return []

        df = pd.DataFrame(rows)
        if df.empty:
            return []

        # Normalize and coerce columns we care about
        df["playerId"] = pd.to_numeric(df.get("playerId"), errors="coerce")
        df = df.dropna(subset=["playerId"])
        df["playerId"] = df["playerId"].astype(int)

        # Ensure columns exist before aggregation
        for col in [
            "name",
            "positionText",
            "teamName",
            "goal",
            "assistTotal",
            "yellowCard",
            "redCard",
            "manOfTheMatch",
            "apps",
            "rating",
            "tournamentId",
        ]:
            if col not in df.columns:
                df[col] = None

        # Aggregate stats across sources per player
        def first_non_empty(series):
            for v in series:
                if v not in (None, "", float("nan")):
                    return str(v)
            return ""

        aggregated = (
            df.groupby("playerId", sort=False)
            .agg(
                name=("name", first_non_empty),
                position_text=("positionText", first_non_empty),
                team_name=("teamName", first_non_empty),
                goals=("goal", "sum"),
                assists=("assistTotal", "sum"),
                yellow_cards=("yellowCard", "sum"),
                red_cards=("redCard", "sum"),
                man_of_the_match=("manOfTheMatch", "sum"),
                appearances=("apps", "sum"),
                rating=("rating", "mean"),
                competitions_count=("tournamentId", "nunique"),
            )
            .reset_index()
        )

        # Convert numeric cols to correct types and fill NaNs
        numeric_cols = {
            "goals": int,
            "assists": int,
            "yellow_cards": int,
            "red_cards": int,
            "man_of_the_match": int,
            "appearances": int,
        }
        for col, typ in numeric_cols.items():
            aggregated[col] = pd.to_numeric(aggregated[col], errors="coerce").fillna(0).astype(int)

        aggregated["rating"] = (
            pd.to_numeric(aggregated["rating"], errors="coerce")
            .fillna(0.0)
            .round(2)
            .astype(float)
        )

        player_ids = aggregated["playerId"].astype(int).tolist()
        existing_players = {
            player.player_id: player
            for player in Player.objects.filter(player_id__in=player_ids)
        }

        normalized: list[dict] = []
        for row in aggregated.to_dict(orient="records"):
            player_id = int(row["playerId"])
            existing = existing_players.get(player_id)

            normalized.append(
                {
                    "player_id": player_id,
                    "name": row.get("name") or "",
                    "position": row.get("position_text") or "",
                    "goals": int(row.get("goals") or 0),
                    "assists": int(row.get("assists") or 0),
                    "yellow_cards": int(row.get("yellow_cards") or 0),
                    "red_cards": int(row.get("red_cards") or 0),
                    "man_of_the_match": int(row.get("man_of_the_match") or 0),
                    "team_name": row.get("team_name") or "",
                    "appearances": int(row.get("appearances") or 0),
                    "rating": float(row.get("rating") or 0.0),
                    "competitions_count": int(row.get("competitions_count") or 0),
                    "previous_rank": existing.rank if existing is not None else None,
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
