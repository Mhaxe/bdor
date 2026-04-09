from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from api.models import Player, FetchRecord
from api.services.data_normalization_service import DataNormalizationService
from api.services.external_stats_service import ExternalStatsService
from api.services.player_ranking_service import PlayerRankingService


class DataNormalizationServiceTests(TestCase):
    def test_normalize_data_reads_player_stats_json(self):
        Player.objects.create(
            player_id=7,
            name="Ada Player",
            position_text="Forward",
            team_name="Test FC",
            goals=4,
            assists=3,
            yellow_cards=1,
            red_cards=0,
            man_of_the_match=3,
            appearances=7,
            rating=7.75,
            rank=2,
        )

        normalized = DataNormalizationService.normalize_data()

        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["player_id"], 7)
        self.assertEqual(normalized[0]["name"], "Ada Player")
        self.assertEqual(normalized[0]["position"], "Forward")
        self.assertEqual(normalized[0]["goals"], 4)
        self.assertEqual(normalized[0]["assists"], 3)
        self.assertEqual(normalized[0]["appearances"], 7)
        self.assertEqual(normalized[0]["rating"], 7.75)
        self.assertEqual(normalized[0]["previous_rank"], None)

    def test_calculate_rank_change(self):
        self.assertEqual(DataNormalizationService.calculate_rank_change(1, None), "same")
        self.assertEqual(DataNormalizationService.calculate_rank_change(1, 3), "up")
        self.assertEqual(DataNormalizationService.calculate_rank_change(3, 1), "down")
        self.assertEqual(DataNormalizationService.calculate_rank_change(2, 2), "same")


class ExternalStatsServiceTests(TestCase):
    def test_should_fetch_today_when_no_players_exist(self):
        self.assertTrue(ExternalStatsService.should_fetch_today())

    def test_should_fetch_today_returns_false_for_fresh_record(self):
        # Create a record that expires in the future.
        FetchRecord.objects.create(
            fetch_next_at=timezone.now() + timedelta(days=1),
            last_fetch_at=timezone.now(),
        )

        self.assertFalse(ExternalStatsService.should_fetch_today())

    def test_should_fetch_today_returns_true_for_stale_record(self):
        # Create a record that is already expired.
        FetchRecord.objects.create(
            fetch_next_at=timezone.now() - timedelta(minutes=1),
            last_fetch_at=timezone.now() - timedelta(days=1),
        )

        self.assertTrue(ExternalStatsService.should_fetch_today())

    def test_sync_all_sources_rolls_back_if_player_upsert_fails(self):
        payloads = {
            "league": [{"playerId": 1, "name": "A"}],
            "ucl": [{"playerId": 2, "name": "B"}],
            "europa": [{"playerId": 3, "name": "C"}],
        }

        with patch.object(
            ExternalStatsService,
            "_fetch_source_payload",
            side_effect=lambda source, scraper=None: payloads[source],
        ), patch.object(
            PlayerRankingService,
            "get_player_rankings",
            side_effect=RuntimeError("upsert failed"),
        ):
            with self.assertRaises(RuntimeError):
                ExternalStatsService.fetch_external_stats()

        self.assertEqual(Player.objects.count(), 0)

    def test_sync_all_sources_keeps_database_clean_if_fetch_fails(self):
        payloads = {
            "league": [{"playerId": 1, "name": "A"}],
        }

        with patch.object(
            ExternalStatsService,
            "_fetch_source_payload",
            side_effect=lambda source, scraper=None: payloads[source]
            if source == "league"
            else (_ for _ in ()).throw(RuntimeError("fetch failed")),
        ):
            with self.assertRaises(RuntimeError):
                ExternalStatsService.fetch_external_stats()

        self.assertEqual(Player.objects.count(), 0)

from django.core.cache import cache

class ClearCacheViewTests(TestCase):
    """Test the clear-cache API view."""

    def test_get_clear_cache_returns_success(self):
        # Set some data in the cache
        cache.set("test_key", "test_value")
        self.assertEqual(cache.get("test_key"), "test_value")

        response = self.client.get("/api/clear-cache/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "Cache cleared successfully")

        # Verify the cache is cleared
        self.assertIsNone(cache.get("test_key"))
