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

    # Stats stored as explicit columns for better query/filter support.
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    man_of_the_match = models.PositiveIntegerField(default=0)
    appearances = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0.0)

    rank = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    previous_rank = models.PositiveIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["rank", "name", "player_id"]

    def __str__(self) -> str:
        return f"{self.name} ({self.player_id})"


class FetchRecord(models.Model):
    fetch_next_at = models.DateTimeField()
    last_fetch_at = models.DateTimeField()
    