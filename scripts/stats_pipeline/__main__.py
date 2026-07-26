"""Entrypoint: `uv run python -m scripts.stats_pipeline`."""

import sys

from .run import run

if __name__ == "__main__":
    sys.exit(run())
