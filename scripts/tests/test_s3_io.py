import json
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from scripts.stats_pipeline import s3_io


def _client_with_objects(objects):
    client = MagicMock()

    def _get_object(Bucket, Key):
        if Key not in objects:
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
        body = MagicMock()
        body.read.return_value = json.dumps(objects[Key]).encode("utf-8")
        return {"Body": body}

    client.get_object.side_effect = _get_object
    return client


def test_get_json_returns_none_when_missing():
    client = _client_with_objects({})
    assert s3_io.get_json(client, "bucket", "missing.json") is None


def test_get_json_returns_parsed_body():
    client = _client_with_objects({"summary/latest_summary.json": {"players": []}})
    result = s3_io.get_json(client, "bucket", "summary/latest_summary.json")
    assert result == {"players": []}


def test_load_previous_ranks_empty_when_no_summary():
    client = _client_with_objects({})
    assert s3_io.load_previous_ranks(client, "bucket") == {}


def test_load_previous_ranks_extracts_rank_by_player_id():
    client = _client_with_objects(
        {s3_io.LATEST_SUMMARY_KEY: {"players": [{"player_id": 1, "rank": 3}, {"player_id": 2, "rank": 1}]}}
    )
    assert s3_io.load_previous_ranks(client, "bucket") == {1: 3, 2: 1}


def test_write_summary_and_manifest_writes_in_order():
    client = MagicMock()
    summary = {"success": True, "total_players": 2, "players": []}

    manifest = s3_io.write_summary_and_manifest(client, "bucket", "2026-07-26", summary)

    keys_written = [call.kwargs["Key"] for call in client.put_object.call_args_list]
    assert keys_written == [
        "summary/2026-07-26_summary.json",
        s3_io.LATEST_SUMMARY_KEY,
        s3_io.LATEST_MANIFEST_KEY,
    ]
    assert manifest["player_count"] == 2
    assert manifest["summary_key"] == "summary/2026-07-26_summary.json"


def test_write_raw_payload_uses_expected_key():
    client = MagicMock()

    key = s3_io.write_raw_payload(client, "bucket", "2026-07-26", "league", [{"a": 1}])

    assert key == "raw/2026-07-26_league.json"
    _, kwargs = client.put_object.call_args
    assert kwargs["Key"] == "raw/2026-07-26_league.json"
    assert json.loads(kwargs["Body"]) == [{"a": 1}]
