from typing import cast

from django.db.models import Manager

from api.models import (
    ExternalStatsBatch,
    PlayerRankingSnapshot,
    RankingSnapshot,
    StatsSource,
)

SUPPORTED_STATS_SOURCES = [
    StatsSource.LEAGUE,
    StatsSource.UCL,
    StatsSource.EUROPA,
]


def _external_stats_batch_manager() -> Manager[ExternalStatsBatch]:
    """Return the default manager for external stats batches."""

    return cast(Manager[ExternalStatsBatch], ExternalStatsBatch._default_manager)


def _ranking_snapshot_manager() -> Manager[RankingSnapshot]:
    """Return the default manager for ranking snapshots."""

    return cast(Manager[RankingSnapshot], RankingSnapshot._default_manager)


def _player_ranking_snapshot_manager() -> Manager[PlayerRankingSnapshot]:
    """Return the default manager for player ranking snapshots."""

    return cast(Manager[PlayerRankingSnapshot], PlayerRankingSnapshot._default_manager)


def get_latest_stats_batch(source: str) -> ExternalStatsBatch | None:
    """Return the latest stored raw stats batch for a source."""

    return (
        _external_stats_batch_manager()
        .filter(source=source)
        .order_by("-fetched_at", "-id")
        .first()
    )


def get_latest_stats_batches() -> list[ExternalStatsBatch]:
    """Return the latest available batch for each supported source."""

    batches: list[ExternalStatsBatch] = []
    for source in SUPPORTED_STATS_SOURCES:
        batch = get_latest_stats_batch(source)
        if batch is not None:
            batches.append(batch)
    return batches


def get_latest_fetched_batch() -> ExternalStatsBatch | None:
    """Return the most recently fetched stats batch across all sources."""

    return _external_stats_batch_manager().order_by("-fetched_at", "-id").first()


def get_previous_rankings() -> list[dict]:
    """Return player rank mappings from the latest ranking snapshot."""

    latest_snapshot = _ranking_snapshot_manager().order_by("-created_at", "-id").first()
    if latest_snapshot is None:
        return []

    return list(
        _player_ranking_snapshot_manager()
        .filter(snapshot=latest_snapshot)
        .order_by("rank", "player_id")
        .values("player_id", "rank")
    )
