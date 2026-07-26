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


def load_config() -> Config:
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
    )
