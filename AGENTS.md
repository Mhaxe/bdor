AGENTS (Repository agent rules and developer conventions)

This document instructs agentic coding assistants how to build, lint, test, and make code-style changes in this repository. Place decisions here so automated agents act consistently.

- Project root: repository uses Django backend + React (Vite + TypeScript) frontend; see `README.md` for high-level dev flows.
- Python target: 3.12+ (see `pyproject.toml`).
- Frontend package file: `frontend/package.json` (vite + bun/npm compatible scripts).

Build / lint / test (commands)
- Create and activate Python venv (first-time):
  ```bash
  python -m venv .venv
  source .venv/bin/activate   # Unix/macOS
  .venv\Scripts\activate    # Windows (PowerShell/CMD)
  pip install -r requirements.txt
  ```
- Run Django dev server (root): `python manage.py runserver` (or use VS Code config in `.vscode/launch.json`).
- Run Django migrations: `python manage.py migrate`.
- Run all backend tests (Django test runner):
  ```bash
  python manage.py test
  ```
- Run a single Django test (module, class or method):
  ```bash
  # Run all tests in a module
  python manage.py test core.tests

  # Run a single TestCase class
  python manage.py test core.tests.MyTestCase

  # Run a single test method
  python manage.py test core.tests.MyTestCase.test_specific_behavior
  ```
- Frontend (from `frontend/`):
  - Dev server (vite): `bun run dev` or `npm run dev` or `pnpm run dev` (depending on environment).
  - Build production bundle: `bun run build` or `npm run build`.
  - Lint: `bun run lint` or `npm run lint` (runs `eslint .` per `frontend/package.json`).

- Package management (preferred tools)
  - Use `uv` for Python dependency and environment workflows when available in the environment. Examples (project-specific `uv` workflows may vary):
    - Install dependencies: `uv install` or follow the repository's `uv` workflow (check `uv.lock`/docs).
    - Run Python commands inside the `uv` environment as the project prefers instead of raw `pip`/`venv` when `uv` is provided.
  - Use `bun` for JavaScript package management and scripts in the frontend. Examples:
    - Install frontend deps: `cd frontend && bun install`.
    - Run scripts: `cd frontend && bun run dev`, `cd frontend && bun run build`, `cd frontend && bun run lint`.

CI / local checks (recommended tools)
- The repository does not enforce specific formatting tools, but agents should prefer non-disruptive checks first:
  - Python: `black` for formatting, `isort` for import ordering, `ruff` or `flake8` for linting.
  - TypeScript/JS: `eslint` (project already has `eslint.config.js`) and `typescript` type check (`tsc -b`).
  - Frontend build uses `vite` and `tsc -b` in `frontend/package.json` build script.

Code style & conventions (for agents to follow)
- General rules
  - Make minimal, focused changes per commit. Follow conventional commit messages (see repo agent config): `feat(scope): short description`, `fix(scope): short description`, `chore:`, `docs:`.
  - Run tests locally for changed code. If adding behavior, include or update tests.
  - Do not commit secrets or large generated files (node_modules, `.venv`, build artifacts). Respect `.gitignore`.

- Python / Django style
  - Formatting: use `black` (88 char line length default is acceptable). Keep code readable; break long expressions over multiple lines rather than deeply nested inline logic.
  - Imports:
    - Use absolute imports for project modules (e.g. `from core.models import Player`).
    - Group imports in this order: standard library, third-party, local application. Add a blank line between groups.
    - Use `isort` to maintain ordering; prefer explicit imports rather than wildcard (`from x import *`).
  - Typing:
    - Prefer type annotations on public functions and complex internal functions. Use `typing` and `pydantic` where appropriate.
    - For Django models and views keep simple annotations (Django ORM types are dynamic); annotate return types for utility functions.
  - Naming:
    - Use `snake_case` for functions and variables, `PascalCase` for classes, `CONSTANTS_UPPER` for constants.
    - Django model field names: `snake_case` and singular (e.g. `player_score`).
  - Error handling:
    - Catch specific exceptions (avoid broad `except:`). Re-raise or wrap exceptions with meaningful context when surfacing to higher levels.
    - For HTTP/API handlers, return proper status codes and include minimal, non-sensitive error messages.
  - Logging:
    - Use the `logging` module with named loggers: `logger = logging.getLogger(__name__)`.
    - Log at appropriate levels (`debug`, `info`, `warning`, `error`, `critical`). Avoid logging secrets.
  - Tests:
    - Use Django `TestCase` for view/model integration tests, plain `unittest` or `pytest`-style for small units. Keep tests deterministic and fast.

- JavaScript / TypeScript / React style (frontend)
  - Formatting & linting: follow `eslint` configuration in `frontend/`. Run `tsc -b` before builds to catch type errors.
  - Files & naming:
    - Components: `PascalCase.tsx` for React components; exports should be named where reasonable.
    - Hooks: `useSomething.ts` and exported hook name `useSomething`.
    - Utility functions: camelCase, colocate with small modules under `src/lib`.
  - Types:
    - Prefer explicit types for public APIs and component props. Use `interface` for props; prefer readonly where applicable.
    - Avoid `any`. If temporarily used, add a `TODO` comment explaining why and add a test or follow-up task.
  - React patterns:
    - Use functional components and hooks (no class components).
    - Keep components small and focused; lift state up only when needed.
    - Use `useEffect` carefully; always include dependencies array; memoize expensive computations with `useMemo` and handlers with `useCallback` when required.
  - Accessibility & UI:
    - Prefer semantic HTML in JSX. Add `aria-*` attributes for interactive components when necessary.
    - When using Tailwind/Tailwind-merge, prefer composing utility classes thoughtfully and use variants consistently.

- Imports and module boundaries (both sides)
  - Keep cross-module imports minimal. Do not import the whole Django project into frontend tooling and vice-versa.
  - Prefer small, well-named functions exported from modules (single responsibility principle).
  - In Python, avoid circular imports by moving shared helpers to `utils/` modules.

- Error handling, exceptions and API surface
  - Backend API endpoints should validate inputs and return structured error responses (JSON with `error` and optionally `code`).
  - Avoid exposing stack traces in production responses. Use logging for debugging and return user-friendly messages.
  - Where long-running tasks exist, prefer background workers (Celery) and return immediate ack + status endpoint.

- Database & Migrations
  - Use `python manage.py makemigrations` / `migrate` for schema changes.
  - Keep migrations small and readable; if generating large data migrations, split schema and data steps.

Agent rules and meta-behavior
- When making code edits, prefer single-file focused patches; avoid rewriting unrelated formatting changes across the repo.
- If adding dependencies, update `requirements.txt` (backend) or `frontend/package.json` and include lockfile update guidance (do not commit `node_modules`).
- Commit style: use Conventional Commits with scopes where appropriate (e.g. `feat(core): add points calculation`). Keep commit messages concise and explain the why.

Repository-specific notes
- VS Code debug: `.vscode/launch.json` already contains a Django debug config.
- Frontend shadcn rules: `frontend/.agents/skills/shadcn/*` contains styling/component rules for the UI library — agents working on the UI should read them.
- Cursor / Copilot rules: none found in this repository (no `.cursor` folder or `.github/copilot-instructions.md`).

Verification checklist for a code change
1. Run unit tests relevant to the change (`python manage.py test path.to.test`).
2. Run linters/formatters: backend `black`/`isort`/`ruff` and frontend `eslint` + `tsc` as applicable.
3. Ensure no secrets were added and `.gitignore` is respected.
4. Run frontend dev build (`bun run build` or `npm run build`) if UI assets changed.
5. Include or update tests for bug fixes and new features.

If blocked, ask one targeted question (exactly one) and include the recommended default action.

— end of file —
