import pandas as pd

from api.models import StatsSource
from api.selectors.stats_selectors import (
    get_latest_stats_batches,
    get_previous_rankings,
)

COLUMNS_TO_SUM = [
    "goals",
    "assists",
    "yellow_cards",
    "red_cards",
    "man_of_the_match",
    "appearances",
]

COLUMNS_OF_INTEREST = [
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

CONVERT_COLUMNS_TO = {
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

POSITION_MAPPING = {
    "Forward": "forward",
    "Midfielder": "midfielder",
    "Defender": "defender",
    "Goalkeeper": "keeper",
}


class DataNormalizationService:
    """Normalize stored raw JSON payloads into ranking-ready player records.

    This service loads the latest raw payload for each stored competition
    source, aligns the external API field names to the internal ranking schema,
    combines rows across sources, and enriches computed rankings with previous
    rank history.
    """

    @staticmethod
    def normalize_data():
        """Load and normalize stored raw JSON payloads into aggregated records.

        Returns:
            list[dict]: Normalized player records ready for player model
            validation and points calculation.
        """

        batches = get_latest_stats_batches()
        source_payloads = {batch.source: batch.raw_payload for batch in batches}

        frames = []
        for source in StatsSource.values:
            payload = source_payloads.get(source, [])
            frame = DataNormalizationService._normalize_source_payload(payload)
            if not frame.empty:
                frames.append(frame)

        if not frames:
            return []

        combined_df = pd.concat(frames, ignore_index=False)
        combined_df = combined_df.groupby("player_id", as_index=False).agg(
            {
                col: "sum" if col in COLUMNS_TO_SUM else "first"
                for col in COLUMNS_OF_INTEREST
            }
        )
        combined_df["rating"] = combined_df["rating"].fillna(0)  # type: ignore[index]

        return combined_df.to_dict(orient="records")  # type: ignore[return-value]

    @staticmethod
    def add_rank_change(player_points_df):
        """Add previous ranking metadata to the current ranking dataframe.

        Args:
            player_points_df: A pandas DataFrame containing scored player
                ranking rows.

        Returns:
            list[dict]: Ranking records enriched with `rank`,
            `previous_rank`, and `rank_change`.
        """

        previous_rankings = get_previous_rankings()
        previous_rankings_df = pd.DataFrame(previous_rankings)

        if not previous_rankings_df.empty:
            player_points_df = player_points_df.merge(
                previous_rankings_df.rename(columns={"rank": "previous_rank"}),
                on="player_id",
                how="left",
            )
        else:
            player_points_df["previous_rank"] = None

        player_points_df["rank"] = range(1, len(player_points_df) + 1)
        player_points_df["rank_change"] = player_points_df.apply(
            lambda row: DataNormalizationService.calculate_rank_change(
                row["rank"], row["previous_rank"]
            ),
            axis=1,
        )

        player_points = player_points_df.to_dict(orient="records")
        for player in player_points:
            if "previous_rank" in player and pd.isna(player["previous_rank"]):
                player["previous_rank"] = None
        return player_points

    @staticmethod
    def calculate_rank_change(current_rank, previous_rank):
        """Return rank change state from current and previous ranking."""

        if previous_rank is None or pd.isna(previous_rank):
            return "same"
        if current_rank < previous_rank:
            return "up"
        if current_rank > previous_rank:
            return "down"
        return "same"

    @staticmethod
    def _normalize_source_payload(payload: list[dict]) -> pd.DataFrame:
        """Convert one raw source payload into a normalized dataframe."""

        if not payload:
            return pd.DataFrame(columns=COLUMNS_OF_INTEREST)

        source_df = pd.DataFrame(payload)
        source_df = source_df.rename(columns=CONVERT_COLUMNS_TO)

        source_cols = [col for col in COLUMNS_OF_INTEREST if col in source_df.columns]
        source_df = source_df[source_cols]

        for column in COLUMNS_OF_INTEREST:
            if column not in source_df.columns:
                source_df[column] = (
                    0 if column in COLUMNS_TO_SUM or column == "rating" else None
                )

        source_df = source_df[COLUMNS_OF_INTEREST]
        source_df["rating"] = source_df["rating"].fillna(0)
        return source_df
