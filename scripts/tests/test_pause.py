"""Covers run()'s PIPELINE_PAUSED short-circuit.

Lives in its own module rather than a test_run.py so it doesn't collide with
the test_run.py added on the ineligible-players branch; fold the two together
whenever both have landed.
"""

import logging
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from scripts.stats_pipeline import run as run_module
from scripts.stats_pipeline.config import Config


def _config(**overrides) -> Config:
    defaults = dict(
        aws_profile="test-profile",
        aws_region="us-east-1",
        s3_bucket="test-bucket",
        sns_alert_topic_arn="arn:aws:sns:us-east-1:000000000000:test",
        stats_url="https://example.test/stats",
        fetch_interval_days=2,
        lock_file="/tmp/test-pipeline.lock",
        log_file="/tmp/test-pipeline.log",
    )
    return Config(**{**defaults, **overrides})


def test_run_skips_everything_when_paused():
    """A paused tick must not touch AWS at all - no S3 client, so no manifest
    read and no per-tick failure alert if credentials break while paused.
    """
    with (
        patch.object(run_module, "load_config", return_value=_config(paused=True)),
        patch.object(run_module, "_configure_logging"),
        patch.object(run_module.s3_io, "get_client") as get_client,
        patch.object(run_module.alerting, "publish_failure") as publish_failure,
    ):
        assert run_module.run() == 0

    get_client.assert_not_called()
    publish_failure.assert_not_called()


def test_run_proceeds_to_the_cadence_check_when_not_paused():
    manifest = {"generated_at": datetime.now(UTC).isoformat()}

    with (
        patch.object(run_module, "load_config", return_value=_config(paused=False)),
        patch.object(run_module, "_configure_logging"),
        patch.object(run_module.s3_io, "get_client", return_value=MagicMock()) as get_client,
        patch.object(run_module.s3_io, "get_json", return_value=manifest),
    ):
        # Just-generated manifest, so the cadence gate declines the fetch - the
        # point is that the flag, not the cadence, is what skipped the S3 work
        # in the test above.
        assert run_module.run() == 0

    get_client.assert_called_once()


def test_run_warns_when_the_flag_value_is_unrecognized(caplog):
    config = _config(paused=False, paused_warning="PIPELINE_PAUSED='treu' is not a recognized boolean")

    with (
        patch.object(run_module, "load_config", return_value=config),
        patch.object(run_module, "_configure_logging"),
        patch.object(run_module.s3_io, "get_client", return_value=MagicMock()),
        patch.object(run_module.s3_io, "get_json", return_value={"generated_at": datetime.now(UTC).isoformat()}),
        caplog.at_level(logging.WARNING, logger="stats_pipeline"),
    ):
        assert run_module.run() == 0

    assert "not a recognized boolean" in caplog.text
