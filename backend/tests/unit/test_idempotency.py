from app.modules.idempotency.service import MemStore, command


def test_repeat_returns_prior_result_without_rerun():
    store = MemStore()
    calls = {"n": 0}

    def op():
        calls["n"] += 1
        return "paid"

    r1 = command(store, "pk1", "hash-a", op)
    assert r1.ok and r1.value == "paid" and calls["n"] == 1
    r2 = command(store, "pk1", "hash-a", op)
    assert r2.ok and r2.value == "paid" and calls["n"] == 1  # not re-run


def test_different_request_same_key_is_conflict():
    store = MemStore()
    command(store, "pk1", "hash-a", lambda: "x")
    r = command(store, "pk1", "hash-b", lambda: "y")
    assert (r.ok, r.conflict) == (False, True)
