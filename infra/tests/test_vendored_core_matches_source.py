"""Guards against infra/lambdas/aggregate_stats/core/ drifting from core/.

The aggregator Lambda needs its own physical copy of core/players.py and
core/points_system.py inside its CodeUri directory (see the module docstring
in infra/lambdas/aggregate_stats/app.py for why this can't be vendored at
`sam build` time). This test fails loudly if someone edits the repo-root
core/ package without updating the vendored copy to match.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VENDORED_CORE = Path(__file__).resolve().parents[1] / "lambdas" / "aggregate_stats" / "core"

VENDORED_FILES = ["__init__.py", "players.py", "points_system.py"]


def test_vendored_core_files_match_source():
    mismatched = []
    for filename in VENDORED_FILES:
        source = (REPO_ROOT / "core" / filename).read_text()
        vendored = (VENDORED_CORE / filename).read_text()
        if source != vendored:
            mismatched.append(filename)

    assert not mismatched, (
        f"infra/lambdas/aggregate_stats/core/{{{', '.join(mismatched)}}} is out of sync "
        f"with core/{{{', '.join(mismatched)}}} - copy the updated file(s) over."
    )
