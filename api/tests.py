from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from api.models import Player
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

    def test_should_fetch_today_returns_false_for_today_player_update(self):
        Player.objects.create(player_id=1, name="A")

        self.assertFalse(ExternalStatsService.should_fetch_today())

    def test_should_fetch_today_returns_true_for_stale_player_update(self):
        player = Player.objects.create(player_id=1, name="A")
        # Use queryset update() to avoid auto_now resetting the field.
        Player.objects.filter(pk=player.pk).update(updated_at=timezone.now() - timedelta(days=1))

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
                ExternalStatsService.sync_all_sources()

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
                ExternalStatsService.sync_all_sources()

        self.assertEqual(Player.objects.count(), 0)
