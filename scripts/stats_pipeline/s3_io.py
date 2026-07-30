"""Thin S3 read/write helpers for the personal-machine stats pipeline.

Keeps the key scheme the removed AWS Lambda pipeline established, so the Django
read path (api/services/s3_summary_service.py) and the bucket's lifecycle rules
(raw/ and summary/ prefixes, infra/template.yaml) keep working unchanged.
"""

import json
import logging
from datetime import UTC, datetime

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

RAW_PREFIX = "raw/"
SUMMARY_PREFIX = "summary/"
LATEST_SUMMARY_KEY = f"{SUMMARY_PREFIX}latest_summary.json"
LATEST_MANIFEST_KEY = f"{SUMMARY_PREFIX}latest_manifest.json"


def get_client(region: str):
    return boto3.client("s3", region_name=region)


def get_json(s3_client, bucket: str, key: str):
    """Return the parsed JSON body at key, or None if the key doesn't exist."""
    try:
        obj = s3_client.get_object(Bucket=bucket, Key=key)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code in ("NoSuchKey", "404"):
            return None
        raise
    return json.loads(obj["Body"].read())


def put_json(s3_client, bucket: str, key: str, data) -> None:
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data).encode("utf-8"),
        ContentType="application/json",
    )


def load_previous_ranks(s3_client, bucket: str) -> dict:
    previous_summary = get_json(s3_client, bucket, LATEST_SUMMARY_KEY)
    if not previous_summary:
        return {}
    return {
        player["player_id"]: player.get("rank")
        for player in previous_summary.get("players", [])
        if player.get("player_id") is not None
    }


def write_raw_payload(s3_client, bucket: str, date_str: str, source: str, payload) -> str:
    key = f"{RAW_PREFIX}{date_str}_{source}.json"
    put_json(s3_client, bucket, key, payload)
    return key


def write_summary_and_manifest(s3_client, bucket: str, date_str: str, summary: dict) -> dict:
    """Write the dated summary, then latest_summary.json, then
    latest_manifest.json last - in that order, so a mid-write crash never
    leaves the manifest pointing at a summary that doesn't exist.
    """
    dated_key = f"{SUMMARY_PREFIX}{date_str}_summary.json"
    put_json(s3_client, bucket, dated_key, summary)
    put_json(s3_client, bucket, LATEST_SUMMARY_KEY, summary)

    manifest = {
        "date": date_str,
        "summary_key": dated_key,
        "generated_at": datetime.now(UTC).isoformat(),
        "player_count": summary.get("total_players", len(summary.get("players", []))),
    }
    put_json(s3_client, bucket, LATEST_MANIFEST_KEY, manifest)
    return manifest
