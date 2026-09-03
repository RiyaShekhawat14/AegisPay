"""Minimal in-process metrics for the control plane, exposed as Prometheus text.

Keeps observability dependency-free: a tiny counter registry (no prometheus_client). Backed by
OTel spans for traces (see observability.py); this only covers the scrape endpoint.
"""

from __future__ import annotations


class Counter:
    def __init__(self, name: str, help: str) -> None:
        self.name = name
        self.help = help
        self._labels: dict[str, int] = {}

    def inc(self, *label_values: str) -> None:
        key = ",".join(label_values)
        self._labels[key] = self._labels.get(key, 0) + 1

    def render(self, label_names: list[str]) -> list[str]:
        out = [f"# HELP {self.name} {self.help}", f"# TYPE {self.name} counter"]
        for key, value in self._labels.items():
            out.append(
                f"{self.name}{{{','.join(k + '="' + v + '"' for k, v in zip(label_names, key.split(',')))}}} {value}"
            )
        return out


requests_total = Counter("http_requests_total", "HTTP requests by path and status")
payments_total = Counter("payments_total", "Payments by status")


def prometheus_text() -> str:
    lines: list[str] = []
    lines += requests_total.render(["path", "status"])
    lines += payments_total.render(["status"])
    return "\n".join(lines) + "\n"
