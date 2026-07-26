"""Orchestrates the personal-machine stats pipeline: cadence check -> lock ->
fetch -> aggregate -> S3 write -> (on error) SNS alert.

Does what the 3 AWS Lambda fetch functions + aggregator Lambda were supposed
to do (infra/lambdas/), but from a residential IP that WhoScored/Cloudflare
doesn't block.
"""

import logging
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from core.players import create_player
from core.stats_aggregation import aggregate_payloads, calculate_rank_change

from . import alerting, s3_io
from .cadence import should_fetch_now
from .config import Config, load_config
from .fetch import FetchSourceError, fetch_all_sources
from .lock import LockHeldError, acquire_lock

logger = logging.getLogger("stats_pipeline")

# Mirrors the deleted DataNormalizationService.POSITION_MAPPING.
POSITION_MAPPING = {
    "Forward": "forward",
    "Midfielder": "midfielder",
    "Defender": "defender",
    "Goalkeeper": "keeper",
}


def _configure_logging(log_file: str) -> None:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)


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


def _do_fetch_and_publish(config: Config, s3_client) -> int:
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    current_stage = "fetch"

    def on_payload_fetched(source: str, payload: list[dict]) -> None:
        s3_io.write_raw_payload(s3_client, config.s3_bucket, date_str, source, payload)

    try:
        source_payloads = fetch_all_sources(config.stats_url, on_payload_fetched=on_payload_fetched)

        current_stage = "aggregate"
        previous_ranks = s3_io.load_previous_ranks(s3_client, config.s3_bucket)
        aggregated = aggregate_payloads(source_payloads)
        player_points = _build_player_points(aggregated, previous_ranks)

        current_stage = "publish"
        summary = {
            "success": True,
            "total_players": len(player_points),
            "players": player_points,
        }
        manifest = s3_io.write_summary_and_manifest(s3_client, config.s3_bucket, date_str, summary)
        logger.info("Wrote summary for %s: %d players", date_str, manifest["player_count"])
        return 0
    except Exception as e:
        source = e.source if isinstance(e, FetchSourceError) else None
        logger.exception("Pipeline run failed at stage=%s source=%s", current_stage, source)
        alerting.publish_failure(config.aws_region, config.sns_alert_topic_arn, current_stage, source, e)
        return 1


def run() -> int:
    config = load_config()
    _configure_logging(config.log_file)

    try:
        s3_client = s3_io.get_client(config.aws_region)
        manifest = s3_io.get_json(s3_client, config.s3_bucket, s3_io.LATEST_MANIFEST_KEY)
    except Exception as e:
        logger.exception("Failed during cadence check (client init or manifest read) - treating as a real failure, not 'not due yet'")
        alerting.publish_failure(config.aws_region, config.sns_alert_topic_arn, "cadence-check", None, e)
        return 1

    now = datetime.now(UTC)
    if not should_fetch_now(manifest, now, config.fetch_interval_days):
        logger.info("Not due yet (last generated_at=%s); skipping.", manifest.get("generated_at") if manifest else None)
        return 0

    logger.info("Fetch is due - acquiring lock and starting run.")
    try:
        with acquire_lock(config.lock_file):
            return _do_fetch_and_publish(config, s3_client)
    except LockHeldError:
        logger.warning("Another run is already in progress; skipping this trigger.")
        return 0
