"""Supervisor de runs en proceso para el MVP.

No sustituye una cola durable: conserva las tareas activas, permite apagado
ordenado y hace explÃ­cito que un reinicio cancela trabajo en curso.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any


class RunTaskManager:
    def __init__(self) -> None:
        self._tasks: set[asyncio.Task[None]] = set()

    def submit(self, coroutine: Coroutine[Any, Any, None]) -> None:
        task: asyncio.Task[None] = asyncio.create_task(coroutine)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def shutdown(self, grace_seconds: int) -> None:
        if not self._tasks:
            return
        done, pending = await asyncio.wait(self._tasks, timeout=grace_seconds)
        del done
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
