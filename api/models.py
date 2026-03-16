from django.db import models


class StatsSource(models.TextChoices):
    """Supported external stats sources."""

    LEAGUE = "league", "League"
    UCL = "ucl", "Champions League"
    EUROPA = "europa", "Europa League"


class Player(models.Model):
    """Stores one stable row per player with combined current stats."""

    player_id = models.PositiveBigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    position_text = models.CharField(max_length=50, blank=True)
    team_id = models.PositiveBigIntegerField(null=True, blank=True)
    team_name = models.CharField(max_length=255, blank=True)
    stats = models.JSONField(default=dict, blank=True)
    rank = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    previous_rank = models.PositiveIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["rank", "name", "player_id"]

    def __str__(self) -> str:
        return f"{self.name} ({self.player_id})"


class RankingSnapshot(models.Model):
    """Represents one generated rankings run."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Ranking snapshot {self.id}"
