"""Metrics registry (Prometheus text) — counters + labels."""

from api.core.metrics import Counter, prometheus_text


def test_counter_increments_with_labels():
    c = Counter("http_requests_total", "requests")
    c.inc("/v1/health", "200")
    c.inc("/v1/health", "200")
    rendered = "\n".join(c.render(["path", "status"]))
    assert "# TYPE http_requests_total counter" in rendered
    assert 'http_requests_total{path="/v1/health",status="200"} 2' in rendered


def test_prometheus_text_lists_both_counters():
    text = prometheus_text()
    assert "# HELP http_requests_total" in text
    assert "# TYPE payments_total counter" in text
