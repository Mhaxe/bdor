from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ExternalStatsBatch",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("league", "League"),
                            ("ucl", "Champions League"),
                            ("europa", "Europa League"),
                        ],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("fetched_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("season_id", models.PositiveIntegerField(blank=True, null=True)),
                ("competition_name", models.CharField(blank=True, max_length=255)),
                ("request_params", models.JSONField(blank=True, default=dict)),
                ("raw_payload", models.JSONField(blank=True, default=list)),
                ("record_count", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ["-fetched_at", "-id"]},
        ),
        migrations.CreateModel(
            name="RankingSnapshot",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="ExternalPlayerStat",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("league", "League"),
                            ("ucl", "Champions League"),
                            ("europa", "Europa League"),
                        ],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("player_id", models.PositiveBigIntegerField(db_index=True)),
                ("name", models.CharField(max_length=255)),
                ("position_text", models.CharField(blank=True, max_length=50)),
                ("team_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("team_name", models.CharField(blank=True, max_length=255)),
                ("goals", models.IntegerField(default=0)),
                ("assists", models.IntegerField(default=0)),
                ("yellow_cards", models.IntegerField(default=0)),
                ("red_cards", models.IntegerField(default=0)),
                ("man_of_the_match", models.IntegerField(default=0)),
                ("appearances", models.IntegerField(default=0)),
                ("rating", models.FloatField(default=0.0)),
                ("raw_row", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "batch",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="player_stats",
                        to="api.externalstatsbatch",
                    ),
                ),
            ],
            options={"ordering": ["source", "name", "player_id"]},
        ),
        migrations.CreateModel(
            name="PlayerRankingSnapshot",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("player_id", models.PositiveBigIntegerField(db_index=True)),
                ("rank", models.PositiveIntegerField()),
                ("previous_rank", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "rank_change",
                    models.CharField(
                        choices=[("up", "Up"), ("down", "Down"), ("same", "Same")],
                        default="same",
                        max_length=10,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("position", models.CharField(max_length=50)),
                ("points", models.FloatField()),
                ("goals", models.IntegerField(default=0)),
                ("assists", models.IntegerField(default=0)),
                ("team_name", models.CharField(blank=True, max_length=255)),
                ("yellow_cards", models.IntegerField(default=0)),
                ("red_cards", models.IntegerField(default=0)),
                ("man_of_the_match", models.IntegerField(default=0)),
                ("rating", models.FloatField(default=0.0)),
                ("appearances", models.IntegerField(default=0)),
                (
                    "snapshot",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="player_rankings",
                        to="api.rankingsnapshot",
                    ),
                ),
            ],
            options={"ordering": ["rank", "player_id"]},
        ),
        migrations.AddConstraint(
            model_name="externalplayerstat",
            constraint=models.UniqueConstraint(
                fields=("batch", "player_id"),
                name="unique_player_per_external_batch",
            ),
        ),
        migrations.AddConstraint(
            model_name="playerrankingsnapshot",
            constraint=models.UniqueConstraint(
                fields=("snapshot", "player_id"),
                name="unique_player_per_ranking_snapshot",
            ),
        ),
    ]
