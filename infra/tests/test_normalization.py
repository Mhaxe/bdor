from normalization import aggregate_payloads, calculate_rank_change


def test_aggregate_payloads_merges_same_player_across_sources():
    league_payload = [
        {
            "playerId": 1, "name": "Alice", "positionText": "Forward", "teamName": "Team A",
            "goal": 5, "assistTotal": 2, "yellowCard": 1, "redCard": 0, "manOfTheMatch": 1,
            "apps": 10, "rating": 7.5, "tournamentId": 2,
        },
    ]
    ucl_payload = [
        {
            "playerId": 1, "name": "Alice", "positionText": "Forward", "teamName": "Team A",
            "goal": 2, "assistTotal": 1, "yellowCard": 0, "redCard": 0, "manOfTheMatch": 0,
            "apps": 4, "rating": 8.0, "tournamentId": 12,
        },
    ]

    result = aggregate_payloads({"league": league_payload, "ucl": ucl_payload, "europa": []})

    assert len(result) == 1
    player = result[0]
    assert player["player_id"] == 1
    assert player["name"] == "Alice"
    assert player["position"] == "Forward"
    assert player["team_name"] == "Team A"
    assert player["goals"] == 7
    assert player["assists"] == 3
    assert player["yellow_cards"] == 1
    assert player["red_cards"] == 0
    assert player["man_of_the_match"] == 1
    assert player["appearances"] == 14
    assert player["rating"] == 7.75
    assert player["competitions_count"] == 2
    assert player["is_eligible"] is True


def test_aggregate_payloads_ineligible_when_no_league_tournament():
    ucl_only = [
        {
            "playerId": 2, "name": "Bob", "positionText": "Defender", "teamName": "Team B",
            "goal": 1, "assistTotal": 0, "yellowCard": 0, "redCard": 0, "manOfTheMatch": 0,
            "apps": 6, "rating": 6.5, "tournamentId": 12,
        },
    ]

    result = aggregate_payloads({"league": [], "ucl": ucl_only, "europa": []})

    assert len(result) == 1
    assert result[0]["is_eligible"] is False


def test_aggregate_payloads_skips_rows_with_invalid_player_id():
    rows = [{"playerId": "not-a-number", "goal": 3}]

    result = aggregate_payloads({"league": rows, "ucl": [], "europa": []})

    assert result == []


def test_aggregate_payloads_handles_missing_fields_gracefully():
    rows = [{"playerId": 3, "tournamentId": 2}]

    result = aggregate_payloads({"league": rows, "ucl": [], "europa": []})

    assert len(result) == 1
    player = result[0]
    assert player["goals"] == 0
    assert player["rating"] == 0.0
    assert player["name"] == ""
    assert player["is_eligible"] is True


def test_calculate_rank_change():
    assert calculate_rank_change(1, None) == "same"
    assert calculate_rank_change(1, 5) == "up"
    assert calculate_rank_change(5, 1) == "down"
    assert calculate_rank_change(3, 3) == "same"
