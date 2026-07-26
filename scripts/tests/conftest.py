"""Ensures the repo root is on sys.path so `core.*` and `scripts.*` import
correctly regardless of pytest's invocation directory - same pattern already
established in infra/tests/conftest.py.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
