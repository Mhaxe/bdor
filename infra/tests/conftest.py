"""Test setup shared by infra/tests/*.

Puts the repo root on sys.path so `core.players`/`core.points_system` import
the same way they will once vendored into the aggregate Lambda's build
artifact, and puts the aggregate_stats lambda dir on sys.path so its sibling
`normalization` module imports normally.

Lambda handler modules are loaded via `load_module()` under unique names
instead of plain `import app`, since both lambdas/fetch_stats/app.py and
lambdas/aggregate_stats/app.py are literally named app.py - a plain import
would have the second import silently reuse the first module cached in
sys.modules under the shared name "app".
"""

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LAMBDAS_DIR = Path(__file__).resolve().parent.parent / "lambdas"

for path in (REPO_ROOT, LAMBDAS_DIR / "aggregate_stats"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def load_module(name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
