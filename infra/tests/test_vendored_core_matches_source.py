"""Guards against infra/lambdas/aggregate_stats/'s vendored copies drifting
from their canonical core/ sources.

The aggregator Lambda needs physical copies of core/players.py,
core/points_system.py, and core/stats_aggregation.py inside its CodeUri
directory (see the module docstrings in infra/lambdas/aggregate_stats/app.py
and core/stats_aggregation.py for why this can't be vendored at `sam build`
time). This test fails loudly if someone edits a repo-root core/ module
without updating the vendored copy to match.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INFRA_DIR = Path(__file__).resolve().parents[1]

# (source path relative to repo root, vendored path relative to infra/)
VENDORED_PAIRS = [
    ("core/__init__.py", "lambdas/aggregate_stats/core/__init__.py"),
    ("core/players.py", "lambdas/aggregate_stats/core/players.py"),
    ("core/points_system.py", "lambdas/aggregate_stats/core/points_system.py"),
    ("core/stats_aggregation.py", "lambdas/aggregate_stats/normalization.py"),
]


def test_vendored_files_match_source():
    mismatched = []
    for source_rel, vendored_rel in VENDORED_PAIRS:
        source = (REPO_ROOT / source_rel).read_text()
        vendored = (INFRA_DIR / vendored_rel).read_text()
        if source != vendored:
            mismatched.append(f"{source_rel} -> {vendored_rel}")

    assert not mismatched, (
        "Vendored file(s) out of sync with their source - copy the updated "
        f"file(s) over: {', '.join(mismatched)}"
    )
