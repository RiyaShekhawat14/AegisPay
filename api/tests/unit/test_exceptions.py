"""Error-code mapping: raw HTTP status -> the standard envelope code.

FastAPI's router-level 404 and uncaught server exceptions don't flow through app handlers,
so this locks down the mapping that the handlers DO use (auth 401, validation 422, etc.).

Note: 404/503 aren't returned by the app's HTTPException handler for router-level errors;
this documents the intended contract and is used when the handler IS invoked (e.g. 401).
"""

from api.core.exceptions import _http_code


def test_common_statuses_map_to_codes():
    assert _http_code(400) == "VALIDATION_ERROR"
    assert _http_code(401) == "AUTHENTICATION_ERROR"
    assert _http_code(403) == "AUTHORIZATION_ERROR"
    assert _http_code(404) == "NOT_FOUND"
    assert _http_code(422) == "VALIDATION_ERROR"
    assert _http_code(429) == "RATE_LIMITED"


def test_unknown_status_falls_back():
    assert _http_code(503) == "HTTP_503"
