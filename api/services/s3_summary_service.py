import json
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


class SummaryNotAvailable(Exception):
    """No S3 summary object exists yet, or it can't be read/parsed."""


class S3SummaryService:
    """Read the latest player-rankings summary produced by the stats pipeline
    (scripts/stats_pipeline/).
    """

    _client = None

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            cls._client = boto3.client("s3", region_name=settings.AWS_REGION)
        return cls._client

    @staticmethod
    def get_latest_summary() -> dict:
        """Fetch and parse the latest summary JSON from S3.

        Raises:
            SummaryNotAvailable: the object doesn't exist yet, can't be
                reached, or its body isn't the expected shape.
        """
        client = S3SummaryService._get_client()
        bucket = settings.S3_SUMMARY_BUCKET
        key = settings.S3_SUMMARY_LATEST_KEY

        try:
            obj = client.get_object(Bucket=bucket, Key=key)
            body = obj["Body"].read()
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code in ("NoSuchKey", "404"):
                raise SummaryNotAvailable(f"s3://{bucket}/{key} does not exist yet") from e
            logger.exception("S3 error fetching summary")
            raise SummaryNotAvailable("S3 read error") from e
        except BotoCoreError as e:
            logger.exception("boto3 error fetching summary")
            raise SummaryNotAvailable("S3 client error") from e

        try:
            data = json.loads(body)
        except (ValueError, UnicodeDecodeError) as e:
            logger.exception("Malformed summary JSON at %s", key)
            raise SummaryNotAvailable("Malformed summary JSON") from e

        if not isinstance(data.get("players"), list):
            raise SummaryNotAvailable("Summary JSON missing 'players' array")

        return data
