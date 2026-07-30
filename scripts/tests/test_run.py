from scripts.stats_pipeline.run import _build_player_points


def _record(player_id, name, *, is_eligible, goals=0, position="Forward"):
    return {
        "player_id": player_id,
        "name": name,
        "position": position,
        "team_name": "Team A",
        "goals": goals,
        "assists": 0,
        "yellow_cards": 0,
        "red_cards": 0,
        "man_of_the_match": 0,
        "appearances": 10,
        "rating": 7.0,
        "competitions_count": 1,
        "is_eligible": is_eligible,
    }


def test_build_player_points_drops_ineligible_players():
    aggregated = [
        _record(1, "Eligible High", is_eligible=True, goals=10),
        _record(2, "Ineligible High", is_eligible=False, goals=99),
        _record(3, "Eligible Low", is_eligible=True, goals=1),
    ]

    result = _build_player_points(aggregated, {})

    assert [p["name"] for p in result] == ["Eligible High", "Eligible Low"]
    assert all(p["is_eligible"] for p in result)


def test_build_player_points_ranks_contiguously_after_filtering():
    # The ineligible player would outscore everyone; dropping it before the
    # sort is what keeps ranks gap-free rather than leaving a hole at its rank.
    aggregated = [
        _record(1, "First", is_eligible=True, goals=10),
        _record(2, "Ringer", is_eligible=False, goals=99),
        _record(3, "Second", is_eligible=True, goals=5),
        _record(4, "Third", is_eligible=True, goals=1),
    ]

    result = _build_player_points(aggregated, {})

    assert [p["rank"] for p in result] == [1, 2, 3]
    assert [p["name"] for p in result] == ["First", "Second", "Third"]


def test_build_player_points_rank_change_uses_previous_ranks():
    aggregated = [
        _record(1, "Climber", is_eligible=True, goals=10),
        _record(2, "Faller", is_eligible=True, goals=1),
    ]

    result = _build_player_points(aggregated, {1: 5, 2: 1})

    by_name = {p["name"]: p for p in result}
    assert by_name["Climber"]["rank"] == 1
    assert by_name["Climber"]["rank_change"] == "up"
    assert by_name["Faller"]["rank"] == 2
    assert by_name["Faller"]["rank_change"] == "down"


def test_build_player_points_skips_records_that_fail_model_validation():
    bad = _record(2, "Bad Position", is_eligible=True, position="Referee")
    aggregated = [_record(1, "Good", is_eligible=True), bad]

    result = _build_player_points(aggregated, {})

    assert [p["name"] for p in result] == ["Good"]
