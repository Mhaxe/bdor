"""Best-effort SNS failure notification via the stack's AlertTopic
(infra/template.yaml). Sole alerting path for the pipeline: the CloudWatch
alarms that used to watch the Lambda pipeline's executions and 403s are gone
along with it, and this script's logs live on the machine it runs on.
"""

import logging
import socket
from datetime import UTC, datetime

import boto3

logger = logging.getLogger(__name__)


def publish_failure(region: str, topic_arn: str, stage: str, source: str | None, error: Exception) -> None:
    """Publish a failure notification. Never raises - a broken alert path
    shouldn't mask the original error or crash the script's error handling.
    """
    subject = f"[bdor-stats-pipeline] local script failure: {stage}"[:100]
    message = (
        f"Stage: {stage}\n"
        f"Source: {source or 'n/a'}\n"
        f"Error: {type(error).__name__}: {error}\n"
        f"Host: {socket.gethostname()}\n"
        f"Time (UTC): {datetime.now(UTC).isoformat()}\n"
    )
    try:
        sns = boto3.client("sns", region_name=region)
        sns.publish(TopicArn=topic_arn, Subject=subject, Message=message)
    except Exception:
        logger.exception("Failed to publish SNS alert (original error: %s)", error)
