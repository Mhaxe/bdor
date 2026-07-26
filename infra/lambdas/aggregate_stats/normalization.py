"""Pure-Python port of DataNormalizationService.normalize_payloads()
(api/services/data_normalization_service.py in the Django app), without pandas.

Merges the raw per-competition WhoScored payloads into one aggregated record
per player. Given the modest row counts involved (a few thousand rows across
all three competitions before grouping), a single defaultdict pass is enough
and avoids packaging pandas (and its layer/cold-start cost) into the Lambda.
"""

from collections import defaultdict

# Tournament IDs for the top 5 leagues (matches SOURCE_CONFIG tournamentOptions
# for the "league" source in app.py). Players must appear in at least one of
# these competitions to be eligible for ranking.
LEAGUE_TOURNAMENT_IDS = frozenset({2, 3, 4, 5, 22})


def _first_non_empty(values):
    for v in values:
        if v not in (None, ""):
            return str(v)
    return ""


def aggregate_payloads(source_payloads: dict) -> list[dict]:
    """Aggregate raw per-source payloads into one record per player.

    Args:
        source_payloads: mapping of source name ("league"/"ucl"/"europa") to
            the raw list of player-row dicts fetched from WhoScored.

    Returns:
        One aggregated dict per player_id, matching the shape previously
        produced by DataNormalizationService.normalize_payloads() minus
        previous_rank (attached separately by the caller from the prior
        summary, since there's no database to read it from here).
    """
    rows = []
    for payload in source_payloads.values():
        rows.extend(payload or [])

    grouped = defaultdict(list)
    for row in rows:
        raw_id = row.get("playerId")
        try:
            player_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        grouped[player_id].append(row)

    aggregated = []
    for player_id, player_rows in grouped.items():
        goals = assists = yellow_cards = red_cards = man_of_the_match = appearances = 0
        ratings = []
        tournament_ids = set()

        for row in player_rows:
            goals += int(row.get("goal") or 0)
            assists += int(row.get("assistTotal") or 0)
            yellow_cards += int(row.get("yellowCard") or 0)
            red_cards += int(row.get("redCard") or 0)
            man_of_the_match += int(row.get("manOfTheMatch") or 0)
            appearances += int(row.get("apps") or 0)

            rating = row.get("rating")
            if rating not in (None, ""):
                try:
                    ratings.append(float(rating))
                except (TypeError, ValueError):
                    pass

            tournament_id = row.get("tournamentId")
            if tournament_id not in (None, ""):
                try:
                    tournament_ids.add(int(tournament_id))
                except (TypeError, ValueError):
                    pass

        mean_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0

        aggregated.append(
            {
                "player_id": player_id,
                "name": _first_non_empty(row.get("name") for row in player_rows),
                "position": _first_non_empty(row.get("positionText") for row in player_rows),
                "goals": goals,
                "assists": assists,
                "yellow_cards": yellow_cards,
                "red_cards": red_cards,
                "man_of_the_match": man_of_the_match,
                "team_name": _first_non_empty(row.get("teamName") for row in player_rows),
                "appearances": appearances,
                "rating": mean_rating,
                "competitions_count": len(tournament_ids),
                "is_eligible": bool(tournament_ids & LEAGUE_TOURNAMENT_IDS),
            }
        )

    return aggregated


def calculate_rank_change(current_rank, previous_rank):
    """Return rank change state from current and previous ranking.

    Direct port of DataNormalizationService.calculate_rank_change()
    (api/services/data_normalization_service.py:169-179).
    """
    if previous_rank is None:
        return "same"
    if current_rank < previous_rank:
        return "up"
    if current_rank > previous_rank:
        return "down"
    return "same"
