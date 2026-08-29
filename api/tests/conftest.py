import pytest


@pytest.fixture(autouse=True)
def _add_packages_to_path():
    """Ensure `api` (and `ai_runtime`) are importable.

    conftest lives at <repo>/api/tests/, so parents[1] = <repo>/api and
    parents[2] = <repo> (the import root for the `api` package).
    """
    import sys
    from pathlib import Path

    here = Path(__file__).resolve()
    for p in (here.parents[1], here.parents[2]):  # api/ and repo root
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
