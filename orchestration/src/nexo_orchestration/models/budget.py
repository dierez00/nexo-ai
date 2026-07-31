"""Contabilidad de presupuesto y deadline del run (`DIE-F1-006`).

La comprobación ocurre **antes** de cada invocación, nunca después. Descubrir
que el run se pasó de presupuesto cuando el proveedor ya cobró es contabilidad,
no control: el gate exige que el 100% de los runs registren costo y que el p95
respete el deadline, y ninguna de las dos cosas se consigue mirando atrás.

El libro es un objeto por run. No se comparte entre ejecuciones ni guarda estado
global: dos runs concurrentes tienen dos libros distintos.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from nexo_contracts import Budgets, ErrorCode, NormalizedError, Outcome


class BudgetExceededError(Exception):
    """No queda presupuesto, tokens o tiempo para la operación solicitada.

    Transporta un `NormalizedError` ya construido para que quien lo capture
    decida con el mismo código estable que registrará en el evento.
    """

    def __init__(self, error: NormalizedError) -> None:
        self.error = error
        super().__init__(f"{error.code.value}: {error.message}")


@dataclass
class BudgetLedger:
    """Lo gastado y lo que queda de un run, en dinero, tokens y tiempo."""

    budgets: Budgets
    elapsed_ms: int = 0
    spent_usd: float = 0.0
    spent_tokens: int = 0
    invocations: int = field(default=0)

    @property
    def remaining_usd(self) -> float:
        return max(0.0, self.budgets.max_cost_usd - self.spent_usd)

    @property
    def remaining_tokens(self) -> int:
        return max(0, self.budgets.max_tokens - self.spent_tokens)

    @property
    def remaining_ms(self) -> int:
        return max(0, self.budgets.deadline_ms - self.elapsed_ms)

    def observe_elapsed(self, elapsed_ms: int) -> None:
        """Registra el tiempo transcurrido del run, medido contra `received_at`."""
        self.elapsed_ms = max(self.elapsed_ms, elapsed_ms)

    def ensure_affordable(self, *, max_cost_usd: float, deadline_ms: int) -> None:
        """Verifica que la próxima invocación quepa. Lanza `BudgetExceededError` si no.

        El deadline se comprueba contra el tiempo restante del run, no contra el
        de la operación: una llamada con 8 s de deadline no puede lanzarse si al
        run le quedan 2 s.
        """
        if self.remaining_ms <= 0:
            raise BudgetExceededError(
                NormalizedError.from_code(
                    ErrorCode.RUN_TIMEOUT,
                    f"el run agotó su deadline de {self.budgets.deadline_ms} ms antes de "
                    f"invocar el modelo",
                    outcome=Outcome.KNOWN_FAILURE,
                )
            )
        if deadline_ms > self.remaining_ms:
            raise BudgetExceededError(
                NormalizedError.from_code(
                    ErrorCode.RUN_TIMEOUT,
                    f"la operación pide {deadline_ms} ms y al run le quedan {self.remaining_ms} ms",
                    outcome=Outcome.KNOWN_FAILURE,
                )
            )
        if max_cost_usd > self.remaining_usd:
            raise BudgetExceededError(
                NormalizedError.from_code(
                    ErrorCode.BUDGET_EXCEEDED,
                    f"la operación reserva {max_cost_usd:.4f} USD y al run le quedan "
                    f"{self.remaining_usd:.4f} USD",
                )
            )
        if self.remaining_tokens <= 0:
            raise BudgetExceededError(
                NormalizedError.from_code(
                    ErrorCode.BUDGET_EXCEEDED,
                    f"el run agotó su presupuesto de {self.budgets.max_tokens} tokens",
                )
            )

    def charge(self, *, cost_usd: float, input_tokens: int, output_tokens: int) -> None:
        """Reconcilia el gasto real después de una invocación, exitosa o no.

        También se cobra un intento fallido: el proveedor cobró igual, y ocultar
        ese costo haría que el presupuesto del run mintiera.
        """
        self.spent_usd += cost_usd
        self.spent_tokens += input_tokens + output_tokens
        self.invocations += 1
