"""Configuration for the personal-machine stats pipeline script.

Loads scripts/stats_pipeline/.env explicitly - deliberately separate from the
Django app's root .env (which carries no AWS credentials at all), so this
personal-machine-only concern never needs to ship with the Django app's
config, and vice versa.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


TRUTHY = frozenset({"1", "true", "yes", "on"})
FALSY = frozenset({"", "0", "false", "no", "off"})


@dataclass(frozen=True)
class Config:
    aws_profile: str
    aws_region: str
    s3_bucket: str
    sns_alert_topic_arn: str
    stats_url: str
    fetch_interval_days: int
    lock_file: str
    log_file: str
    paused: bool = False
    # Set when PIPELINE_PAUSED held an unrecognized value. Carried on the
    # config rather than logged from here because load_config() runs before
    # _configure_logging(), so anything logged at this point would reach only
    # cron's stdout - exactly the blind spot this flag exists to avoid.
    paused_warning: str | None = None


def parse_paused(raw: str | None) -> tuple[bool, str | None]:
    """Parse PIPELINE_PAUSED into (paused, warning).

    Fails open - an unrecognized value means NOT paused, with a warning -
    matching should_fetch_now()'s behavior in cadence.py. A pipeline that
    silently stops publishing is worse than one that runs when you meant to
    pause it: the unwanted fetch is visible in the log and costs one cycle,
    whereas a silent freeze looks identical to a working pause and can go
    unnoticed for weeks.
    """
    value = (raw or "").strip().lower()
    if value in TRUTHY:
        return True, None
    if value in FALSY:
        return False, None
    return False, (
        f"PIPELINE_PAUSED={raw!r} is not a recognized boolean "
        f"(use one of {sorted(TRUTHY)} to pause, {sorted(FALSY - {''})} to resume); "
        "treating the pipeline as NOT paused"
    )


def load_config() -> Config:
    paused, paused_warning = parse_paused(os.environ.get("PIPELINE_PAUSED"))
    # AWS_PROFILE is read from scripts/stats_pipeline/.env into os.environ by
    # load_dotenv() above; every boto3 client created anywhere in this
    # process picks it up automatically via the SDK's default credential chain.
    return Config(
        aws_profile=os.environ.get("AWS_PROFILE", ""),
        aws_region=os.environ.get("AWS_REGION", "us-east-1"),
        s3_bucket=os.environ["S3_BUCKET"],
        sns_alert_topic_arn=os.environ["SNS_ALERT_TOPIC_ARN"],
        stats_url=os.environ["STATS_URL"],
        fetch_interval_days=int(os.environ.get("FETCH_INTERVAL_DAYS", "2")),
        lock_file=os.environ.get("LOCK_FILE", "/tmp/bdor-stats-pipeline.lock"),
        log_file=os.environ.get("LOG_FILE", "logs/stats_pipeline.log"),
        paused=paused,
        paused_warning=paused_warning,
    )
