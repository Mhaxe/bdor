"""Fetch one competition's player stats from WhoScored and store the raw payload in S3.

Three separate Lambda function resources (FetchLeagueFunction, FetchUclFunction,
FetchEuropaFunction) share this handler, differentiated by the SOURCE env var.
Deliberately invoked one at a time (with jitter waits) by the Step Functions state
machine, never in parallel, to preserve the anti-IP-blocking behavior of the
original single-process implementation this replaces
(api/services/external_stats_service.py in the Django app).
"""

import json
import logging
import os
from datetime import UTC, datetime

import boto3
import cloudscraper

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

STATS_URL = os.environ["STATS_URL"]
SOURCE = os.environ["SOURCE"]
S3_BUCKET = os.environ["S3_BUCKET"]
RAW_PREFIX = os.environ.get("RAW_PREFIX", "raw/")

s3 = boto3.client("s3")

# Mirrors SOURCE_CONFIG in api/services/external_stats_service.py:21-63.
SOURCE_CONFIG = {
    "league": {
        "category": "summary",
        "subcategory": "all",
        "statsAccumulationType": "0",
        "isCurrent": "true",
        "tournamentOptions": "2,3,4,5,22",
        "sortBy": "Rating",
        "field": "Overall",
        "isMinApp": "false",
        "numberOfPlayersToPick": "2300",
    },
    "ucl": {
        "category": "summary",
        "subcategory": "all",
        "statsAccumulationType": "0",
        "isCurrent": "true",
        "stageId": "24797",
        "tournamentOptions": "12",
        "sortBy": "Rating",
        "field": "Overall",
        "isMinApp": "false",
        "numberOfPlayersToPick": "774",
    },
    "europa": {
        "category": "summary",
        "subcategory": "all",
        "statsAccumulationType": "0",
        "isCurrent": "true",
        "stageId": "24799",
        "tournamentOptions": "30",
        "sortBy": "Rating",
        "field": "Overall",
        "isMinApp": "false",
        "numberOfPlayersToPick": "789",
    },
}


def _fetch_payload(source: str) -> list[dict]:
    config = SOURCE_CONFIG[source]
    scraper = cloudscraper.create_scraper()

    # Diagnostic logging (kept from the original Django implementation): identify
    # which egress IP / Cloudflare PoP this invocation uses, to correlate 403s
    # with routing rather than code. See api/services/external_stats_service.py:145-160.
    try:
        egress_ip = scraper.get("https://api.ipify.org", timeout=10).text.strip()
    except Exception:
        egress_ip = "unknown"

    response = scraper.get(STATS_URL, params=config, headers={})
    logger.info(
        "External stats response: source=%s status=%s egress_ip=%s cf_ray=%s server=%s",
        source,
        response.status_code,
        egress_ip,
        response.headers.get("CF-RAY", "-"),
        response.headers.get("Server", "-"),
    )
    response.raise_for_status()
    return response.json().get("playerTableStats", [])


def handler(event, context):
    if SOURCE not in SOURCE_CONFIG:
        raise ValueError(f"Unknown SOURCE '{SOURCE}', expected one of {list(SOURCE_CONFIG)}")

    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    payload = _fetch_payload(SOURCE)

    key = f"{RAW_PREFIX}{date_str}_{SOURCE}.json"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(payload).encode("utf-8"),
        ContentType="application/json",
    )

    logger.info("Wrote %d player rows for source=%s to s3://%s/%s", len(payload), SOURCE, S3_BUCKET, key)

    return {"source": SOURCE, "s3_key": key, "player_count": len(payload)}
