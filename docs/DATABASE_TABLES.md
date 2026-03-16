# Database Tables

This document describes the main Django database tables used by the backend.

The current rankings pipeline stores external football statistics in the database,
normalizes them into player rows, and persists ranking history as snapshots.

## Overview

The ranking flow works like this:

1. External source data is fetched from the API
2. The raw payload for each source is stored in `ExternalStatsBatch`
3. Query-friendly normalized player rows are stored in `ExternalPlayerStat`
4. Rankings are computed from the latest stored source payloads
5. Each ranking run is stored in `RankingSnapshot`
6. Each player's result in that run is stored in `PlayerRankingSnapshot`

## Table: `api_externalstatsbatch`

Backed by the Django model `ExternalStatsBatch` in `api/models.py`.

Purpose:
- Stores one fetched raw payload for a single source such as `league`, `ucl`, or `europa`
- Acts as the source-of-truth record for what the external API returned at a given time

Important fields:
- `source`: which source the payload came from
- `fetched_at`: when the payload was stored
- `season_id`: season identifier from the external payload when available
- `competition_name`: external competition name when available
- `request_params`: request params used for the fetch
- `raw_payload`: full JSON payload returned by the API for that source
- `record_count`: number of raw rows in the payload

Why this table exists:
- preserves the original fetched JSON for traceability and debugging
- lets the app avoid depending on CSV files
- makes it possible to inspect historical fetches later

Typical usage:
- load the latest stored payload for each source
- inspect raw API output when normalization logic changes

## Table: `api_externalplayerstat`

Backed by the Django model `ExternalPlayerStat` in `api/models.py`.

Purpose:
- Stores normalized, query-friendly player stats derived from one `ExternalStatsBatch`
- Makes per-player analytics and inspection easier without re-parsing the raw payload every time

Important fields:
- `batch_id`: foreign key to `ExternalStatsBatch`
- `source`: source label duplicated for easier filtering
- `player_id`: external player identifier
- `name`: player name
- `position_text`: source position label such as `Forward`
- `team_id`: external team identifier
- `team_name`: team name
- `goals`
- `assists`
- `yellow_cards`
- `red_cards`
- `man_of_the_match`
- `appearances`
- `rating`
- `raw_row`: original normalized source row for this player

Constraint:
- one row per `(batch_id, player_id)`

Why this table exists:
- gives a relational representation of each fetched player stat row
- supports analytics and admin inspection without reading the full batch JSON
- keeps a source-level historical record of player stats per fetch

Typical usage:
- inspect player stats from one source batch
- compare normalized row values with ranking results

## Table: `api_rankingsnapshot`

Backed by the Django model `RankingSnapshot` in `api/models.py`.

Purpose:
- Represents one complete ranking computation run
- Serves as the parent record for a set of ranked player results

Important fields:
- `created_at`: when the ranking run was stored

Why this table exists:
- groups player ranking rows into a single historical snapshot
- gives a time-based record of ranking runs

Typical usage:
- list ranking runs over time
- compare one ranking run with another

## Table: `api_playerrankingsnapshot`

Backed by the Django model `PlayerRankingSnapshot` in `api/models.py`.

Purpose:
- Stores one player's ranking result inside a specific `RankingSnapshot`
- This is the core historical ranking table for analytics

Important fields:
- `snapshot_id`: foreign key to `RankingSnapshot`
- `player_id`: external player identifier
- `rank`: rank in that snapshot
- `previous_rank`: previous known rank at the time this snapshot was computed
- `rank_change`: `up`, `down`, or `same`
- `name`
- `position`
- `points`
- `goals`
- `assists`
- `team_name`
- `yellow_cards`
- `red_cards`
- `man_of_the_match`
- `rating`
- `appearances`

Constraint:
- one row per `(snapshot_id, player_id)`

Why this table exists:
- stores the full ranking history for every player
- supports rank-transition analysis without needing an extra history table
- captures both the player's score and placement at the time of the ranking run

Typical usage:
- get one player's ranking history by filtering on `player_id`
- calculate rank transitions over time by ordering rows by `snapshot.created_at`
- find climbers, fallers, and historical peaks

## Enums Used By The Tables

### `StatsSource`

Used by:
- `ExternalStatsBatch.source`
- `ExternalPlayerStat.source`

Current values:
- `league`
- `ucl`
- `europa`

### `RankChange`

Used by:
- `PlayerRankingSnapshot.rank_change`

Current values:
- `up`
- `down`
- `same`

## Relationship Summary

- One `ExternalStatsBatch` has many `ExternalPlayerStat` rows
- One `RankingSnapshot` has many `PlayerRankingSnapshot` rows
- Rankings are computed from the latest stored source payloads, not directly from one single source batch

## Analytics Notes

If you need rank transitions for one player, use `PlayerRankingSnapshot`.

You do not need a separate rank-history table because rank history is already captured by:
- `player_id`
- `snapshot_id`
- `rank`
- `previous_rank`
- `rank_change`

To reconstruct a player's ranking history:
- filter `PlayerRankingSnapshot` by `player_id`
- join to `RankingSnapshot`
- order by `RankingSnapshot.created_at`

## Future Documentation Updates

Update this file whenever:
- a new analytics table is added
- a model field changes meaning
- the ranking pipeline starts linking snapshots to ingestion runs more explicitly
