import json
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from django.core.cache import cache
from django.test import TestCase, override_settings

from api.services.s3_summary_service import S3SummaryService, SummaryNotAvailable
from api.views import RANKINGS_CACHE_KEY


class ClearCacheViewTests(TestCase):
    """Test the admin-gated clear-cache API view."""

    def setUp(self):
        cache.clear()

    def test_get_clear_cache_without_token_returns_forbidden(self):
        with override_settings(ADMIN_API_TOKEN="secret-token"):
            response = self.client.get("/api/cc/")

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.data["success"])

    def test_get_clear_cache_with_wrong_token_returns_forbidden(self):
        with override_settings(ADMIN_API_TOKEN="secret-token"):
            response = self.client.get("/api/cc/", HTTP_X_ADMIN_TOKEN="wrong-token")

        self.assertEqual(response.status_code, 403)

    def test_get_clear_cache_with_valid_token_clears_rankings_cache(self):
        cache.set(RANKINGS_CACHE_KEY, {"success": True}, timeout=60)

        with override_settings(ADMIN_API_TOKEN="secret-token"):
            response = self.client.get("/api/cc/", HTTP_X_ADMIN_TOKEN="secret-token")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertIsNone(cache.get(RANKINGS_CACHE_KEY))

    def test_get_clear_cache_disabled_when_no_token_configured(self):
        with override_settings(ADMIN_API_TOKEN=None):
            response = self.client.get("/api/cc/")

        self.assertEqual(response.status_code, 403)


class S3SummaryServiceTests(TestCase):
    def setUp(self):
        S3SummaryService._client = None

    def tearDown(self):
        S3SummaryService._client = None

    @patch("api.services.s3_summary_service.boto3.client")
    def test_get_latest_summary_returns_parsed_json(self, mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        body = MagicMock()
        body.read.return_value = json.dumps(
            {"success": True, "total_players": 1, "players": [{"player_id": 1}]}
        ).encode("utf-8")
        mock_client.get_object.return_value = {"Body": body}

        with override_settings(S3_SUMMARY_BUCKET="test-bucket", S3_SUMMARY_LATEST_KEY="summary/latest_summary.json"):
            result = S3SummaryService.get_latest_summary()

        self.assertEqual(result["total_players"], 1)
        mock_client.get_object.assert_called_once_with(Bucket="test-bucket", Key="summary/latest_summary.json")

    @patch("api.services.s3_summary_service.boto3.client")
    def test_get_latest_summary_raises_when_key_missing(self, mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.get_object.side_effect = ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")

        with self.assertRaises(SummaryNotAvailable):
            S3SummaryService.get_latest_summary()

    @patch("api.services.s3_summary_service.boto3.client")
    def test_get_latest_summary_raises_on_malformed_json(self, mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        body = MagicMock()
        body.read.return_value = b"not valid json"
        mock_client.get_object.return_value = {"Body": body}

        with self.assertRaises(SummaryNotAvailable):
            S3SummaryService.get_latest_summary()

    @patch("api.services.s3_summary_service.boto3.client")
    def test_get_latest_summary_raises_when_players_key_missing(self, mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        body = MagicMock()
        body.read.return_value = json.dumps({"success": True}).encode("utf-8")
        mock_client.get_object.return_value = {"Body": body}

        with self.assertRaises(SummaryNotAvailable):
            S3SummaryService.get_latest_summary()


class RankingsViewTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch("api.views.S3SummaryService.get_latest_summary")
    def test_get_rankings_returns_200_from_s3_summary(self, mock_get_summary):
        mock_get_summary.return_value = {
            "success": True,
            "total_players": 1,
            "players": [{"player_id": 1, "name": "Alice", "points": 10, "rank": 1}],
        }

        response = self.client.get("/api/rankings/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["total_players"], 1)
        self.assertEqual(cache.get(RANKINGS_CACHE_KEY)["total_players"], 1)

    @patch("api.views.S3SummaryService.get_latest_summary")
    def test_get_rankings_returns_503_and_does_not_cache_when_summary_not_available(self, mock_get_summary):
        mock_get_summary.side_effect = SummaryNotAvailable("not there yet")

        response = self.client.get("/api/rankings/")

        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["status"], "not_ready")
        self.assertIsNone(cache.get(RANKINGS_CACHE_KEY))

    def test_get_rankings_serves_from_cache_without_hitting_s3(self):
        cache.set(
            RANKINGS_CACHE_KEY,
            {"success": True, "total_players": 1, "players": [{"player_id": 1}]},
            timeout=60,
        )

        with patch("api.views.S3SummaryService.get_latest_summary") as mock_get_summary:
            response = self.client.get("/api/rankings/")

        mock_get_summary.assert_not_called()
        self.assertEqual(response.status_code, 200)
