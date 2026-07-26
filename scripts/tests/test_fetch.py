from unittest.mock import MagicMock, patch

import pytest
import requests

from scripts.stats_pipeline.fetch import FetchSourceError, fetch_all_sources


def _mock_response(status_code=200, payload=None, headers=None, text="1.2.3.4"):
    response = MagicMock()
    response.status_code = status_code
    response.headers = headers or {}
    response.text = text
    response.json.return_value = {"playerTableStats": payload or []}
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"{status_code} error", response=response
        )
    else:
        response.raise_for_status.return_value = None
    return response


def test_fetch_all_sources_happy_path():
    scraper = MagicMock()
    scraper.get.side_effect = [
        _mock_response(200),  # ipify for league
        _mock_response(200, payload=[{"playerId": 1}]),  # league real request
        _mock_response(200),  # ipify for ucl
        _mock_response(200, payload=[{"playerId": 2}]),  # ucl real request
        _mock_response(200),  # ipify for europa
        _mock_response(200, payload=[{"playerId": 3}]),  # europa real request
    ]
    fetched = []

    with (
        patch("scripts.stats_pipeline.fetch.cloudscraper.create_scraper", return_value=scraper),
        patch("scripts.stats_pipeline.fetch.time.sleep"),
    ):
        result = fetch_all_sources(
            "https://example.test/stats", on_payload_fetched=lambda s, p: fetched.append(s)
        )

    assert result == {
        "league": [{"playerId": 1}],
        "ucl": [{"playerId": 2}],
        "europa": [{"playerId": 3}],
    }
    assert fetched == ["league", "ucl", "europa"]


def test_fetch_all_sources_raises_fetch_source_error_naming_the_failed_source():
    scraper = MagicMock()
    scraper.get.side_effect = [
        _mock_response(200),  # ipify for league
        _mock_response(200, payload=[{"playerId": 1}]),  # league succeeds
        _mock_response(200),  # ipify for ucl
        _mock_response(403),  # ucl fails
    ]
    fetched = []

    with (
        patch("scripts.stats_pipeline.fetch.cloudscraper.create_scraper", return_value=scraper),
        patch("scripts.stats_pipeline.fetch.time.sleep"),
        pytest.raises(FetchSourceError) as exc_info,
    ):
        fetch_all_sources("https://example.test/stats", on_payload_fetched=lambda s, p: fetched.append(s))

    assert exc_info.value.source == "ucl"
    assert isinstance(exc_info.value.original, requests.exceptions.HTTPError)
    # league had already succeeded and been handed to the callback before ucl failed.
    assert fetched == ["league"]


def test_fetch_all_sources_does_not_wrap_non_http_errors():
    """Only requests.exceptions.HTTPError (from response.raise_for_status())
    gets wrapped/tagged with its source - other failures (network errors,
    etc.) propagate as-is, since they're not something raise_for_status
    raises and aren't specifically an HTTP-status failure.
    """
    scraper = MagicMock()
    scraper.get.side_effect = [
        _mock_response(200),  # ipify for league
        requests.exceptions.ConnectionError("network unreachable"),  # league real request fails
    ]

    with (
        patch("scripts.stats_pipeline.fetch.cloudscraper.create_scraper", return_value=scraper),
        patch("scripts.stats_pipeline.fetch.time.sleep"),
        pytest.raises(requests.exceptions.ConnectionError),
    ):
        fetch_all_sources("https://example.test/stats")
