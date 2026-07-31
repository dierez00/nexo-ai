"""Tests del token bucket in-app y del trace_id opaco válido."""

from __future__ import annotations

from nexo_api.core.middleware import new_trace_id
from nexo_api.core.rate_limit import RateLimiter


def test_rate_limiter_allows_burst_then_blocks() -> None:
    limiter = RateLimiter(burst=3, per_minute=60)
    assert limiter.check("tenant:user") == 0.0
    assert limiter.check("tenant:user") == 0.0
    assert limiter.check("tenant:user") == 0.0
    blocked = limiter.check("tenant:user")
    assert blocked > 0.0  # cuarto en ráfaga → bloqueado con espera sugerida


def test_rate_limiter_is_per_key() -> None:
    limiter = RateLimiter(burst=1, per_minute=60)
    assert limiter.check("a") == 0.0
    assert limiter.check("b") == 0.0  # otra key tiene su propio bucket
    assert limiter.check("a") > 0.0


def test_new_trace_id_is_canonically_opaque() -> None:
    # El validador canónico rechaza corridas de >=10 dígitos; validamos 1000 veces.
    import re

    long_digits = re.compile(r"\d{10,}")
    for _ in range(1000):
        trace = new_trace_id()
        assert trace.startswith("trace_")
        assert not long_digits.search(trace)
