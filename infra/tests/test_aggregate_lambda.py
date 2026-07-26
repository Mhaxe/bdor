import json
import os
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from conftest import LAMBDAS_DIR, load_module

os.environ.setdefault("S3_BUCKET", "test-bucket")

aggregate_app = load_module("aggregate_stats_app_module", LAMBDAS_DIR / "aggregate_stats" / "app.py")


def _s3_get_object_side_effect(objects):
    def _get_object(Bucket, Key):
        if Key not in objects:
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
        body = MagicMock()
        body.read.return_value = json.dumps(objects[Key]).encode("utf-8")
        return {"Body": body}

    return _get_object


def test_handler_ranks_players_and_writes_summary_to_s3():
    league_rows = [
        {
            "playerId": 1, "name": "Alice", "positionText": "Forward", "teamName": "Team A",
            "goal": 10, "assistTotal": 5, "yellowCard": 0, "redCard": 0, "manOfTheMatch": 2,
            "apps": 20, "rating": 7.8, "tournamentId": 2,
        },
        {
            "playerId": 2, "name": "Bob", "positionText": "Goalkeeper", "teamName": "Team B",
            "goal": 0, "assistTotal": 0, "yellowCard": 0, "redCard": 0, "manOfTheMatch": 1,
            "apps": 18, "rating": 7.0, "tournamentId": 3,
        },
    ]
    objects = {
        "raw/2026-07-26_league.json": league_rows,
        "raw/2026-07-26_ucl.json": [],
        "raw/2026-07-26_europa.json": [],
        "summary/latest_summary.json": {
            "success": True,
            "total_players": 1,
            "players": [{"player_id": 2, "rank": 1}],
        },
    }
    event = {
        "results": {
            "league": {"s3_key": "raw/2026-07-26_league.json"},
            "ucl": {"s3_key": "raw/2026-07-26_ucl.json"},
            "europa": {"s3_key": "raw/2026-07-26_europa.json"},
        }
    }

    fake_s3 = MagicMock()
    fake_s3.get_object.side_effect = _s3_get_object_side_effect(objects)

    with patch.object(aggregate_app, "s3", fake_s3):
        manifest = aggregate_app.handler(event, None)

    assert manifest["player_count"] == 2

    put_calls = {call.kwargs["Key"]: call.kwargs["Body"] for call in fake_s3.put_object.call_args_list}
    assert "summary/latest_summary.json" in put_calls
    assert "summary/latest_manifest.json" in put_calls
    assert manifest["summary_key"] in put_calls

    summary = json.loads(put_calls["summary/latest_summary.json"])
    assert summary["total_players"] == 2

    players_by_id = {p["player_id"]: p for p in summary["players"]}
    # Alice: 10 goals*4 + 5 assists*3 + 2 MOTM*5 + ceil(20*7.8) = 40+15+10+156 = 221
    assert players_by_id[1]["points"] == 221
    assert players_by_id[1]["rank"] == 1
    # Bob (keeper): 1 MOTM*15 + ceil(18*7.0) = 15+126 = 141, dropped from rank 1 -> 2
    assert players_by_id[2]["points"] == 141
    assert players_by_id[2]["rank"] == 2
    assert players_by_id[2]["rank_change"] == "down"


def test_handler_handles_missing_previous_summary():
    objects = {
        "raw/2026-07-26_league.json": [
            {
                "playerId": 5, "name": "Carol", "positionText": "Midfielder", "teamName": "Team C",
                "goal": 1, "assistTotal": 1, "yellowCard": 0, "redCard": 0, "manOfTheMatch": 0,
                "apps": 10, "rating": 6.5, "tournamentId": 4,
            },
        ],
        "raw/2026-07-26_ucl.json": [],
        "raw/2026-07-26_europa.json": [],
        # no summary/latest_summary.json - first-ever run
    }
    event = {
        "results": {
            "league": {"s3_key": "raw/2026-07-26_league.json"},
            "ucl": {"s3_key": "raw/2026-07-26_ucl.json"},
            "europa": {"s3_key": "raw/2026-07-26_europa.json"},
        }
    }

    fake_s3 = MagicMock()
    fake_s3.get_object.side_effect = _s3_get_object_side_effect(objects)

    with patch.object(aggregate_app, "s3", fake_s3):
        manifest = aggregate_app.handler(event, None)

    assert manifest["player_count"] == 1
    put_calls = {call.kwargs["Key"]: call.kwargs["Body"] for call in fake_s3.put_object.call_args_list}
    summary = json.loads(put_calls["summary/latest_summary.json"])
    assert summary["players"][0]["previous_rank"] is None
    assert summary["players"][0]["rank_change"] == "same"
