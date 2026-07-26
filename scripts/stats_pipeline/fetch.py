"""Fetch the 3 WhoScored payloads sequentially using ONE shared cloudscraper
session for the whole run - unlike the AWS Lambda pipeline
(infra/lambdas/fetch_stats/app.py), which creates a new session per Lambda
invocation (one per source) and loses Cloudflare session/cookie continuity
between requests. Running all 3 fetches in one process restores the original
single-process session-continuity behavior (matching the pre-migration
Django ExternalStatsService.fetch_external_stats()) - a genuine improvement
over what the Lambda architecture could achieve.
"""

import logging
import random
import time
from collections.abc import Callable

import cloudscraper

logger = logging.getLogger(__name__)

SOURCES = ("league", "ucl", "europa")

# Mirrors infra/lambdas/fetch_stats/app.py's SOURCE_CONFIG.
SOURCE_CONFIG: dict[str, dict[str, str]] = {
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


def _fetch_one(scraper: "cloudscraper.CloudScraper", stats_url: str, source: str) -> list[dict]:
    config = SOURCE_CONFIG[source]

    # Diagnostic logging: identify which egress IP / Cloudflare PoP this run
    # uses. Kept from the original Django/Lambda implementations - it's the
    # signal that would catch this residential IP eventually getting flagged
    # the same way AWS Lambda's IP was.
    try:
        egress_ip = scraper.get("https://api.ipify.org", timeout=10).text.strip()
    except Exception:
        egress_ip = "unknown"

    response = scraper.get(stats_url, params=config, headers={})
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


def fetch_all_sources(
    stats_url: str,
    on_payload_fetched: Callable[[str, list[dict]], None] | None = None,
) -> dict[str, list[dict]]:
    """Fetch all 3 sources sequentially with a single shared cloudscraper session.

    Args:
        stats_url: the WhoScored stats endpoint.
        on_payload_fetched: optional callback(source, payload) invoked right
            after each source is fetched successfully, e.g. to write the raw
            payload to S3 immediately for audit-trail parity before moving
            on to the next source.

    Raises on the first failure. Any sources already fetched before the
    failure have already been handed to on_payload_fetched, so their raw
    payloads aren't lost even though the run as a whole is aborted.
    """
    scraper = cloudscraper.create_scraper()
    results: dict[str, list[dict]] = {}

    for i, source in enumerate(SOURCES):
        if i > 0:
            delay = random.uniform(1, 5)
            logger.debug("Sleeping %.2fs before fetching next source", delay)
            time.sleep(delay)

        payload = _fetch_one(scraper, stats_url, source)
        results[source] = payload
        if on_payload_fetched is not None:
            on_payload_fetched(source, payload)

    return results
