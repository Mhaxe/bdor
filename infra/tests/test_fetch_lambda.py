import json
import os
from unittest.mock import MagicMock, patch

from conftest import LAMBDAS_DIR, load_module

os.environ.setdefault("STATS_URL", "https://example.test/stats")
os.environ.setdefault("SOURCE", "league")
os.environ.setdefault("S3_BUCKET", "test-bucket")

fetch_app = load_module("fetch_stats_app_module", LAMBDAS_DIR / "fetch_stats" / "app.py")


def _mock_response(status_code=200, payload=None, headers=None, text="203.0.113.1"):
    response = MagicMock()
    response.status_code = status_code
    response.headers = headers or {}
    response.text = text
    response.json.return_value = {"playerTableStats": payload or []}
    response.raise_for_status.return_value = None
    return response


def test_handler_writes_raw_payload_to_s3():
    scraper = MagicMock()
    scraper.get.side_effect = [
        _mock_response(200),  # egress-ip lookup
        _mock_response(200, payload=[{"playerId": 1}], headers={"CF-RAY": "abc", "Server": "cloudflare"}),
    ]

    with patch.object(fetch_app, "s3") as fake_s3, \
         patch("cloudscraper.create_scraper", return_value=scraper):
        result = fetch_app.handler({}, None)

    assert result["source"] == "league"
    assert result["player_count"] == 1
    fake_s3.put_object.assert_called_once()
    _, kwargs = fake_s3.put_object.call_args
    assert kwargs["Bucket"] == "test-bucket"
    assert kwargs["Key"].endswith("_league.json")
    assert json.loads(kwargs["Body"]) == [{"playerId": 1}]


def test_handler_raises_and_does_not_write_on_http_error():
    scraper = MagicMock()
    error_response = _mock_response(403)
    error_response.raise_for_status.side_effect = Exception("403 Forbidden")
    scraper.get.side_effect = [_mock_response(200), error_response]

    with patch.object(fetch_app, "s3") as fake_s3, \
         patch("cloudscraper.create_scraper", return_value=scraper):
        try:
            fetch_app.handler({}, None)
            raised = False
        except Exception:
            raised = True

    assert raised
    fake_s3.put_object.assert_not_called()


def test_handler_falls_back_to_unknown_egress_ip_on_ipify_failure():
    scraper = MagicMock()
    scraper.get.side_effect = [
        Exception("network error"),
        _mock_response(200, payload=[{"playerId": 1}]),
    ]

    with patch.object(fetch_app, "s3") as fake_s3, \
         patch("cloudscraper.create_scraper", return_value=scraper):
        result = fetch_app.handler({}, None)

    assert result["player_count"] == 1
    fake_s3.put_object.assert_called_once()
