# BalonRank

BalonRank is a full-stack football player rankings application built with Django and React. It aggregates player statistics from major European competitions, calculates a position-aware points score, stores the latest ranking snapshot, and presents the results in a searchable frontend.

## What The App Does

- Fetches player stats from supported external competitions
- Merges a player's records across competitions into one combined profile
- Calculates points using different scoring rules for forwards, midfielders, defenders, and goalkeepers
- Persists the latest rank and previous-rank movement
- Serves a rankings table, FAQ page, Django admin, and JSON API from the same Django app

Supported competitions currently shown in the product:

- Premier League
- La Liga
- Bundesliga
- Serie A
- Ligue 1
- Champions League
- Europa League

## Architecture

This repository uses a Django backend and a React + Vite + TypeScript frontend.

Django is responsible for:

- API endpoints under `/api/`
- Serving the built frontend in integrated mode
- Admin access under `/admin/`
- Persisting player data and request/error logs

React is responsible for:

- Rankings UI at `/rankings`
- FAQ UI at `/faqs`
- A simple landing page at `/`

The current integration pattern is explicit server-side routes that return the frontend shell for the rankings and FAQ pages, rather than a catch-all SPA route.

## Ranking Flow

1. A request hits `/api/rankings/`.
2. The backend checks whether player stats have already been refreshed today.
3. If the data is stale, the backend fetches multiple stat sources in parallel.
4. Raw payloads are normalized into one record per player.
5. Position-specific scoring rules are applied.
6. Rankings are sorted and saved with current and previous rank metadata.
7. The frontend renders the returned player list in a filterable, paginated table.

The main scoring inputs include:

- Goals
- Assists
- Yellow cards
- Red cards
- Man of the Match awards
- Appearances
- Average rating

## Project Structure

```text
bdor/
├── api/                 # DRF API endpoints, services, models, tests
├── balon_dor/           # Django project settings and root URLs
├── core/                # Domain logic: players, points system, frontend views
├── docs/                # Supporting documentation
├── frontend/            # React + Vite + TypeScript application
├── manage.py            # Django entry point
├── pyproject.toml       # Python project metadata and dependencies
├── requirements.txt     # Minimal backend requirements
└── uv.lock              # uv lockfile
```

Important areas:

- `api/services/external_stats_service.py`: external fetch and refresh orchestration
- `api/services/data_normalization_service.py`: payload merging and normalization
- `api/services/player_ranking_service.py`: scoring, sorting, rank persistence
- `core/points_system.py`: position-based scoring rules
- `core/players.py`: validated player domain models
- `frontend/src/Rankings.tsx`: rankings table UI
- `frontend/src/FAQs.tsx`: scoring and competitions UI

## Requirements

- Python 3.12+
- Bun
- SQLite for local development by default

Optional but preferred:

- `uv` for Python environment and dependency workflows

## Setup

### Backend

If you are using a virtual environment manually:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you are using `uv`, follow the repository's `uv` workflow instead.

### Frontend

```bash
cd frontend
bun install
cd ..
```

### Database

```bash
python manage.py migrate
```

Optional:

```bash
python manage.py createsuperuser
```

## Development

### Option 1: Two-server development

Backend:

```bash
python manage.py runserver
```

Frontend:

```bash
cd frontend
bun run dev
```

Typical local URLs:

- Django: `http://localhost:8000`
- Vite: `http://localhost:5173`

### Option 2: Integrated Django-served frontend

Build the frontend first:

```bash
cd frontend
bun run build
cd ..
```

Then run Django:

```bash
python manage.py runserver
```

## Commands

### Backend

```bash
python manage.py runserver
python manage.py migrate
python manage.py makemigrations
python manage.py test
python manage.py check
python manage.py collectstatic --noinput
```

Run a targeted backend test:

```bash
python manage.py test api.tests
python manage.py test core.tests
python manage.py test path.to.TestCase
python manage.py test path.to.TestCase.test_method
```

### Frontend

Run these in `frontend/`:

```bash
bun run dev
bun run build
bun run lint
bun run preview
```

## API Surface

Current API endpoints:

- `GET /api/rankings/`
  Returns the computed player rankings payload used by the frontend.

- `GET /api/faqs/`
  Returns the current points system configuration used to populate the FAQ page.

- `GET /api/error/`
  Returns recent logged application errors as plain text.

## Frontend Routes

- `/`
  Placeholder landing page

- `/rankings`
  Main player rankings experience

- `/faqs`
  Explanation of scoring rules and supported competitions

- `/admin/`
  Django admin

## Technology Stack

Backend:

- Django
- Django REST Framework
- Pydantic
- Pandas
- cloudscraper
- WhiteNoise
- SQLite locally, PostgreSQL-ready dependencies present

Frontend:

- React 19
- TypeScript
- Vite
- React Router
- TanStack Query
- TanStack Table
- Tailwind CSS

## Notes

- Rankings are cached at the API layer.
- External stats fetching is skipped if the current day's data is already stored.
- Rank movement is derived from the previously stored rank snapshot.
- The repository contains some starter-template remnants, but the active product surface is the football rankings flow.

## Verification Checklist

For code changes in this repository, the expected local checks are:

1. Run relevant Django tests.
2. Run frontend linting and type-safe build if the UI changed.
3. Build the frontend when integrated Django delivery is affected.

Common commands:

```bash
python manage.py test
cd frontend && bun run lint
cd frontend && bun run build
```

## Documentation

- `docs/DEPLOYMENT.md`
- `docs/EXPLICIT_ROUTES.md`
- `docs/CBV_REFERENCE.md`



