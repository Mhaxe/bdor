"""Aggregate the 3 raw per-competition payloads into a final ranked summary.

Ports the old DataNormalizationService.normalize_payloads() merge logic
(pure-Python, see normalization.py) and PlayerRankingService.get_player_rankings()
ranking/points assignment - both originally in the Django app, now deleted
there since fetching and ranking live entirely in this Lambda pipeline.

The `core/` package here (players.py, points_system.py) is a committed copy
of the repo-root core/players.py and core/points_system.py, not built/copied
at `sam build` time: SAM always stages just this function's CodeUri directory
into a scratch build location, so a Makefile step reaching outside CodeUri
(e.g. "../../../core/") fails in both local and --use-container builds. Keep
this copy in sync by hand when the repo-root core/ package changes -
infra/tests/test_vendored_core_matches_source.py fails the build if they drift.

Writes the final ranked shape directly to S3 so the Django read path
(api/services/s3_summary_service.py) can serve it with no further ranking
computation needed on each request.
"""

import json
import logging
import os
from datetime import UTC, datetime

import boto3
from botocore.exceptions import ClientError
from normalization import aggregate_payloads, calculate_rank_change

from core.players import create_player

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

S3_BUCKET = os.environ["S3_BUCKET"]
SUMMARY_PREFIX = os.environ.get("SUMMARY_PREFIX", "summary/")
LATEST_SUMMARY_KEY = f"{SUMMARY_PREFIX}latest_summary.json"
LATEST_MANIFEST_KEY = f"{SUMMARY_PREFIX}latest_manifest.json"

# Mirrors POSITION_MAPPING in api/services/data_normalization_service.py:5-10.
POSITION_MAPPING = {
    "Forward": "forward",
    "Midfielder": "midfielder",
    "Defender": "defender",
    "Goalkeeper": "keeper",
}

s3 = boto3.client("s3")


def _get_json(key: str) -> dict | list | None:
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            return None
        raise
    return json.loads(obj["Body"].read())


def _load_previous_ranks() -> dict:
    previous_summary = _get_json(LATEST_SUMMARY_KEY)
    if not previous_summary:
        return {}
    return {
        player["player_id"]: player.get("rank")
        for player in previous_summary.get("players", [])
        if player.get("player_id") is not None
    }


def _build_player_points(aggregated: list[dict], previous_ranks: dict) -> list[dict]:
    player_points = []
    for record in aggregated:
        record["position"] = POSITION_MAPPING.get(record["position"], record["position"])
        try:
            player = create_player(record)
        except Exception:
            logger.exception("Skipping player_id=%s: failed to build player model", record.get("player_id"))
            continue

        player_points.append(
            {
                "player_id": record["player_id"],
                "name": record["name"],
                "position": record["position"],
                "points": player.get_points(),
                "goals": player.goals,
                "assists": player.assists,
                "team_name": record["team_name"],
                "yellow_cards": player.yellow_cards,
                "red_cards": player.red_cards,
                "man_of_the_match": player.man_of_the_match,
                "rating": player.rating,
                "appearances": player.appearances,
                "competitions_count": record["competitions_count"],
                "is_eligible": record["is_eligible"],
                "previous_rank": previous_ranks.get(record["player_id"]),
            }
        )

    player_points.sort(key=lambda p: p["points"], reverse=True)
    for index, player in enumerate(player_points):
        current_rank = index + 1
        player["rank"] = current_rank
        player["rank_change"] = calculate_rank_change(current_rank, player["previous_rank"])

    return player_points


def handler(event, context):
    results = event["results"]
    source_payloads = {
        "league": _get_json(results["league"]["s3_key"]) or [],
        "ucl": _get_json(results["ucl"]["s3_key"]) or [],
        "europa": _get_json(results["europa"]["s3_key"]) or [],
    }

    previous_ranks = _load_previous_ranks()
    aggregated = aggregate_payloads(source_payloads)
    player_points = _build_player_points(aggregated, previous_ranks)

    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    generated_at = datetime.now(UTC).isoformat()

    summary = {
        "success": True,
        "total_players": len(player_points),
        "players": player_points,
    }
    dated_summary_key = f"{SUMMARY_PREFIX}{date_str}_summary.json"
    body = json.dumps(summary).encode("utf-8")

    s3.put_object(Bucket=S3_BUCKET, Key=dated_summary_key, Body=body, ContentType="application/json")
    s3.put_object(Bucket=S3_BUCKET, Key=LATEST_SUMMARY_KEY, Body=body, ContentType="application/json")

    manifest = {
        "date": date_str,
        "summary_key": dated_summary_key,
        "generated_at": generated_at,
        "player_count": len(player_points),
    }
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=LATEST_MANIFEST_KEY,
        Body=json.dumps(manifest).encode("utf-8"),
        ContentType="application/json",
    )

    logger.info("Wrote summary for %s: %d players", date_str, len(player_points))

    return manifest
