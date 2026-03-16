from django.db import models


class StatsSource(models.TextChoices):
    """Supported external stats sources."""

    LEAGUE = "league", "League"
    UCL = "ucl", "Champions League"
    EUROPA = "europa", "Europa League"


class RankChange(models.TextChoices):
    """Rank change states persisted for ranking snapshots."""

    UP = "up", "Up"
    DOWN = "down", "Down"
    SAME = "same", "Same"


class ExternalStatsBatch(models.Model):
    """Stores one fetched raw payload for a competition source."""

    source = models.CharField(max_length=20, choices=StatsSource.choices, db_index=True)
    fetched_at = models.DateTimeField(auto_now_add=True, db_index=True)
    season_id = models.PositiveIntegerField(null=True, blank=True)
    competition_name = models.CharField(max_length=255, blank=True)
    request_params = models.JSONField(default=dict, blank=True)
    raw_payload = models.JSONField(default=list, blank=True)
    record_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-fetched_at", "-id"]

    def __str__(self) -> str:
        return f"{self.source} batch {self.id}"


class ExternalPlayerStat(models.Model):
    """Stores normalized player stats extracted from a raw external batch."""

    batch = models.ForeignKey(
        ExternalStatsBatch,
        on_delete=models.CASCADE,
        related_name="player_stats",
    )
    source = models.CharField(max_length=20, choices=StatsSource.choices, db_index=True)
    player_id = models.PositiveBigIntegerField(db_index=True)
    name = models.CharField(max_length=255)
    position_text = models.CharField(max_length=50, blank=True)
    team_id = models.PositiveBigIntegerField(null=True, blank=True)
    team_name = models.CharField(max_length=255, blank=True)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    yellow_cards = models.IntegerField(default=0)
    red_cards = models.IntegerField(default=0)
    man_of_the_match = models.IntegerField(default=0)
    appearances = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    raw_row = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["source", "name", "player_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["batch", "player_id"],
                name="unique_player_per_external_batch",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.source})"


class RankingSnapshot(models.Model):
    """Represents one generated rankings run."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Ranking snapshot {self.id}"


class PlayerRankingSnapshot(models.Model):
    """Stores one ranked player row inside a ranking snapshot."""

    snapshot = models.ForeignKey(
        RankingSnapshot,
        on_delete=models.CASCADE,
        related_name="player_rankings",
    )
    player_id = models.PositiveBigIntegerField(db_index=True)
    rank = models.PositiveIntegerField()
    previous_rank = models.PositiveIntegerField(null=True, blank=True)
    rank_change = models.CharField(
        max_length=10,
        choices=RankChange.choices,
        default=RankChange.SAME,
    )
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=50)
    points = models.FloatField()
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    team_name = models.CharField(max_length=255, blank=True)
    yellow_cards = models.IntegerField(default=0)
    red_cards = models.IntegerField(default=0)
    man_of_the_match = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    appearances = models.IntegerField(default=0)

    class Meta:
        ordering = ["rank", "player_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["snapshot", "player_id"],
                name="unique_player_per_ranking_snapshot",
            )
        ]

    def __str__(self) -> str:
        return f"#{self.rank} {self.name}"
