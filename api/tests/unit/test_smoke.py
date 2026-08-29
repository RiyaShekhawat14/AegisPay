"""Phase 0 smoke test: the application module must import and expose a usable FastAPI app.

This is intentionally dependency-minimal. It does not touch the database or network; it only
proves the Control Plane can be imported, which catches broken imports, missing config wiring,
and startup-time errors before any domain feature runs.
"""


def test_app_imports_and_lists_health_route() -> None:
    from api.main import app

    assert app is not None
    assert app.title == "AegisPay Control Plane"

    paths = {route.path for route in app.routes}
    assert "/v1/health" in paths
    assert "/v1/me" in paths
