"""Rate limiting in-app (token bucket).

Limitación conocida: el estado vive en el proceso, así que NO se comparte entre
réplicas. Es suficiente para la demo/single-instance; un despliegue multi-réplica
requeriría estado compartido (fuera del alcance actual — ver doc de Dani).
"""

from __future__ import annotations

import time
from threading import Lock


class RateLimiter:
    def __init__(self, burst: int, per_minute: int) -> None:
        self._capacity = float(burst)
        self._refill_per_second = per_minute / 60.0
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = Lock()

    def check(self, key: str) -> float:
        """Consume un token para `key`. Devuelve 0.0 si se permite; si no, los
        segundos sugeridos de espera (> 0)."""
        now = time.monotonic()
        with self._lock:
            tokens, last = self._buckets.get(key, (self._capacity, now))
            tokens = min(self._capacity, tokens + (now - last) * self._refill_per_second)
            if tokens >= 1.0:
                self._buckets[key] = (tokens - 1.0, now)
                return 0.0
            self._buckets[key] = (tokens, now)
            return (1.0 - tokens) / self._refill_per_second
