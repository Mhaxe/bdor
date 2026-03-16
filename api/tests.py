from datetime import timedelta
from typing import cast
from unittest.mock import patch

from django.db.models import Manager
from django.test import TestCase
from django.utils import timezone

from api.models import ExternalPlayerStat, ExternalStatsBatch
from api.services.data_normalization_service import DataNormalizationService
from api.services.external_stats_service import ExternalStatsService
from api.services.ranking_snapshot_service import RankingSnapshotService


class DataNormalizationServiceTests(TestCase):
    def test_normalize_source_payload_maps_api_fields(self):
        payload = [
            {
                "playerId": 7,
                "name": "Ada Player",
                "goal": 3,
                "assistTotal": 2,
                "positionText": "Forward",
                "yellowCard": 1,
                "redCard": 0,
                "manOfTheMatch": 4,
                "teamName": "Test FC",
                "apps": 5,
                "rating": 7.5,
            }
        ]

        frame = DataNormalizationService._normalize_source_payload(payload)

        self.assertEqual(frame.iloc[0]["player_id"], 7)
        self.assertEqual(frame.iloc[0]["goals"], 3)
        self.assertEqual(frame.iloc[0]["assists"], 2)
        self.assertEqual(frame.iloc[0]["position"], "Forward")
        self.assertEqual(frame.iloc[0]["team_name"], "Test FC")
        self.assertEqual(frame.iloc[0]["appearances"], 5)

    def test_add_rank_change_uses_latest_snapshot_history(self):
        RankingSnapshotService.create_snapshot(
            [
                {
                    "player_id": 1,
                    "rank": 2,
                    "previous_rank": None,
                    "rank_change": "same",
                    "name": "First",
                    "position": "forward",
                    "points": 10,
                    "goals": 1,
                    "assists": 1,
                    "team_name": "A",
                    "yellow_cards": 0,
                    "red_cards": 0,
                    "man_of_the_match": 0,
                    "rating": 7.0,
                    "appearances": 1,
                },
                {
                    "player_id": 2,
                    "rank": 1,
                    "previous_rank": None,
                    "rank_change": "same",
                    "name": "Second",
                    "position": "midfielder",
                    "points": 12,
                    "goals": 2,
                    "assists": 1,
                    "team_name": "B",
                    "yellow_cards": 0,
                    "red_cards": 0,
                    "man_of_the_match": 0,
                    "rating": 7.2,
                    "appearances": 1,
                },
            ]
        )

        player_points_df = DataNormalizationService._normalize_source_payload(
            [
                {
                    "playerId": 1,
                    "name": "First",
                    "goal": 1,
                    "assistTotal": 1,
                    "positionText": "Forward",
                    "yellowCard": 0,
                    "redCard": 0,
                    "manOfTheMatch": 0,
                    "teamName": "A",
                    "apps": 1,
                    "rating": 7.0,
                },
                {
                    "playerId": 2,
                    "name": "Second",
                    "goal": 2,
                    "assistTotal": 1,
                    "positionText": "Midfielder",
                    "yellowCard": 0,
                    "redCard": 0,
                    "manOfTheMatch": 0,
                    "teamName": "B",
                    "apps": 1,
                    "rating": 7.2,
                },
            ]
        )
        player_points_df["points"] = [20, 15]
        player_points_df = player_points_df.sort_values("points", ascending=False)

        rankings = DataNormalizationService.add_rank_change(player_points_df)

        self.assertEqual(rankings[0]["player_id"], 1)
        self.assertEqual(rankings[0]["previous_rank"], 2)
        self.assertEqual(rankings[0]["rank_change"], "up")
        self.assertEqual(rankings[1]["previous_rank"], 1)
        self.assertEqual(rankings[1]["rank_change"], "down")

    def test_normalize_data_aggregates_latest_batches(self):
        batch_manager = cast(Manager, ExternalStatsBatch._default_manager)

        batch_manager.create(
            source="league",
            raw_payload=[
                {
                    "playerId": 7,
                    "name": "Ada Player",
                    "goal": 3,
                    "assistTotal": 2,
                    "positionText": "Forward",
                    "yellowCard": 1,
                    "redCard": 0,
                    "manOfTheMatch": 1,
                    "teamName": "Test FC",
                    "apps": 5,
                    "rating": 7.5,
                }
            ],
            record_count=1,
        )
        batch_manager.create(
            source="ucl",
            raw_payload=[
                {
                    "playerId": 7,
                    "name": "Ada Player",
                    "goal": 1,
                    "assistTotal": 1,
                    "positionText": "Forward",
                    "yellowCard": 0,
                    "redCard": 0,
                    "manOfTheMatch": 2,
                    "teamName": "Test FC",
                    "apps": 2,
                    "rating": 8.0,
                }
            ],
            record_count=1,
        )

        normalized = DataNormalizationService.normalize_data()

        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["player_id"], 7)
        self.assertEqual(normalized[0]["goals"], 4)
        self.assertEqual(normalized[0]["assists"], 3)
        self.assertEqual(normalized[0]["man_of_the_match"], 3)
        self.assertEqual(normalized[0]["appearances"], 7)


class RankingSnapshotServiceTests(TestCase):
    def test_create_snapshot_persists_rankings(self):
        snapshot = RankingSnapshotService.create_snapshot(
            [
                {
                    "player_id": 10,
                    "rank": 1,
                    "previous_rank": None,
                    "rank_change": "same",
                    "name": "Snapshot Player",
                    "position": "forward",
                    "points": 99.0,
                    "goals": 10,
                    "assists": 5,
                    "team_name": "Snapshot FC",
                    "yellow_cards": 1,
                    "red_cards": 0,
                    "man_of_the_match": 2,
                    "rating": 8.2,
                    "appearances": 9,
                }
            ]
        )

        ranking_snapshot_manager = cast(Manager, snapshot.__class__._default_manager)
        self.assertEqual(ranking_snapshot_manager.count(), 1)


class ExternalStatsServiceTests(TestCase):
    def test_should_fetch_today_when_no_batches_exist(self):
        self.assertTrue(ExternalStatsService.should_fetch_today())

    def test_should_fetch_today_returns_false_for_today_batch(self):
        batch_manager = cast(Manager, ExternalStatsBatch._default_manager)
        batch_manager.create(source="league", raw_payload=[], record_count=0)
        batch_manager.create(source="ucl", raw_payload=[], record_count=0)
        batch_manager.create(source="europa", raw_payload=[], record_count=0)

        self.assertFalse(ExternalStatsService.should_fetch_today())

    def test_should_fetch_today_returns_true_for_stale_batch(self):
        batch_manager = cast(Manager, ExternalStatsBatch._default_manager)
        stale_batch = batch_manager.create(
            source="league", raw_payload=[], record_count=0
        )
        batch_manager.create(source="ucl", raw_payload=[], record_count=0)
        batch_manager.create(source="europa", raw_payload=[], record_count=0)
        stale_batch.fetched_at = timezone.now() - timedelta(days=1)
        stale_batch.save(update_fields=["fetched_at"])

        self.assertTrue(ExternalStatsService.should_fetch_today())

    def test_sync_all_sources_rolls_back_if_storage_fails(self):
        payloads = {
            "league": [{"playerId": 1, "name": "A"}],
            "ucl": [{"playerId": 2, "name": "B"}],
            "europa": [{"playerId": 3, "name": "C"}],
        }

        with (
            patch.object(
                ExternalStatsService,
                "_fetch_source_payload",
                side_effect=lambda source: payloads[source],
            ),
            patch.object(
                ExternalStatsService,
                "_create_normalized_rows",
                side_effect=[None, RuntimeError("boom")],
            ),
        ):
            with self.assertRaises(RuntimeError):
                ExternalStatsService.sync_all_sources()

        batch_manager = cast(Manager, ExternalStatsBatch._default_manager)
        player_stat_manager = cast(Manager, ExternalPlayerStat._default_manager)

        self.assertEqual(batch_manager.count(), 0)
        self.assertEqual(player_stat_manager.count(), 0)

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

        batch_manager = cast(Manager, ExternalStatsBatch._default_manager)
        player_stat_manager = cast(Manager, ExternalPlayerStat._default_manager)

        self.assertEqual(batch_manager.count(), 0)
        self.assertEqual(player_stat_manager.count(), 0)
