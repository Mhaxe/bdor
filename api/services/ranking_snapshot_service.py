from django.db import transaction

from api.models import PlayerRankingSnapshot, RankingSnapshot


class RankingSnapshotService:
    """Persist computed rankings as immutable snapshot records."""

    @staticmethod
    def create_snapshot(rankings: list[dict]) -> RankingSnapshot:
        """Create a ranking snapshot and its ranked player rows."""

        with transaction.atomic():
            snapshot = RankingSnapshot.objects.create()
            PlayerRankingSnapshot.objects.bulk_create(
                [
                    PlayerRankingSnapshot(
                        snapshot=snapshot,
                        player_id=ranking["player_id"],
                        rank=ranking["rank"],
                        previous_rank=ranking.get("previous_rank"),
                        rank_change=ranking["rank_change"],
                        name=ranking["name"],
                        position=ranking["position"],
                        points=ranking["points"],
                        goals=ranking["goals"],
                        assists=ranking["assists"],
                        team_name=ranking.get("team_name") or "",
                        yellow_cards=ranking["yellow_cards"],
                        red_cards=ranking["red_cards"],
                        man_of_the_match=ranking["man_of_the_match"],
                        rating=ranking["rating"],
                        appearances=ranking["appearances"],
                    )
                    for ranking in rankings
                ]
            )
        return snapshot
