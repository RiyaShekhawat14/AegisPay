import pytest


@pytest.fixture(autouse=True)
def _add_app_to_path():
    """Ensure `app` is importable when running pytest from the repo root."""
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
