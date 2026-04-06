from datetime import datetime, timedelta
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
        self.assertEqual(normalized[0]["previous_rank"], 2)

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
            side_effect=lambda source: payloads[source],
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
            side_effect=lambda source: payloads[source]
            if source == "league"
            else (_ for _ in ()).throw(RuntimeError("fetch failed")),
        ):
            with self.assertRaises(RuntimeError):
                ExternalStatsService.fetch_external_stats()

        self.assertEqual(Player.objects.count(), 0)


class ExternalStatsViewTests(TestCase):
    """Test standard response behavior for the external-stats API view."""

    def test_get_external_stats_returns_success(self):
        # We patch sync_if_stale to avoid true network requests during unit tests.
        with patch(
            "api.services.external_stats_service.ExternalStatsService.sync_if_stale"
        ) as mock_sync:
            mock_sync.return_value = [
                {"player_id": 1, "name": "Test Player", "points": 10}
            ]

            response = self.client.get("/api/external-stats/")

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.data["success"])
            self.assertEqual(len(response.data["players"]), 1)
            self.assertEqual(response.data["players"][0]["name"], "Test Player")

    def test_get_external_stats_returns_error_on_failure(self):
        with patch(
            "api.services.external_stats_service.ExternalStatsService.sync_if_stale",
            side_effect=Exception("sync failed"),
        ):
            response = self.client.get("/api/external-stats/")

            self.assertEqual(response.status_code, 500)
            self.assertFalse(response.data["success"])
            self.assertEqual(response.data["error"], "sync failed")


class ExternalStatsSchedulingTests(TestCase):
    """Test the next-Thursday scheduling logic in ExternalStatsService."""

    def test_get_next_thursday_logic(self):
        # 2024-04-01 is Monday (0)
        # 2024-04-04 is Thursday (3)
        monday = datetime(2024, 4, 1)
        next_thu = ExternalStatsService.get_next_thursday(monday)
        self.assertEqual(next_thu.weekday(), 3)
        self.assertEqual(next_thu.day, 4)

        # 2024-04-04 is Thursday (3)
        # Next Thursday should be 2024-04-11
        thursday = datetime(2024, 4, 4)
        next_thu = ExternalStatsService.get_next_thursday(thursday)
        self.assertEqual(next_thu.weekday(), 3)
        self.assertEqual(next_thu.day, 11)

        # 2024-04-05 is Friday (4)
        # Next Thursday should be 2024-04-11
        friday = datetime(2024, 4, 5)
        next_thu = ExternalStatsService.get_next_thursday(friday)
        self.assertEqual(next_thu.weekday(), 3)
        self.assertEqual(next_thu.day, 11)
