"""Redactor cerrado (F1.12).

Recibe `VerifiedFacts`, canal, locale y perfil. Nada más (`DIE-F1-093`).

**No tiene puertos de RAG ni de MCP** (`DIE-F1-094`), y eso no es una regla que
cumpla por disciplina: su constructor no los acepta. Si mañana alguien quisiera
que el redactor consultara una fuente para «completar» una respuesta, tendría
que cambiar la firma, y ese cambio se ve en una revisión. Un puerto inyectado
«por si acaso» no se ve.

El invariante que sostiene el gate de alucinación es el **self-check estructural**
(`DIE-F1-098`): la respuesta redactada se compara contra los hechos del snapshot,
y todo número o monto que aparezca en el texto y no esté en ningún hecho es un
claim nuevo. No se compara prosa —eso sería frágil y subjetivo— sino las
entidades que se pueden inventar sin que se note: cifras.

Si el modelo falla, hay **plantilla determinista** (`DIE-F1-099`). Una plantilla
es peor prosa y exactamente la misma información, que es el intercambio correcto.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from nexo_contracts import (
    Channel,
    ErrorCode,
    FactCategory,
    ModelTaskKind,
    NexoModel,
    NormalizedError,
    Profile,
    SelfCheckResult,
    VerificationStatus,
    VerifiedFact,
    VerifiedFacts,
)
from nexo_contracts.model_gateway import ModelInvocation

from .prompts import Prompt, load_prompt

if TYPE_CHECKING:  # pragma: no cover - solo para tipos
    from nexo_orchestration.models import ModelCallContext, ModelGateway

PURPOSE = "write_answer"
OUTPUT_CONTRACT = "drafted_answer"

# Números con al menos dos dígitos. Los de un dígito producen demasiados falsos
# positivos («paso 1», «tipo A») y son justamente los que menos daño hacen si se
# inventan.
_NUMBER = re.compile(r"\d[\d\s.,]*\d")


class DraftedAnswer(NexoModel):
    """Salida del redactor. Solo texto: no puede transportar hechos ni acciones."""

    answer: str = Field(max_length=20000)
    short_answer: str = Field(
        default="",
        max_length=1200,
        description="Versión breve para canales de texto (`DIE-F1-097`).",
    )


@dataclass(frozen=True)
class WritingOutcome:
    """Respuesta redactada más la verificación de que no inventó nada."""

    answer: str
    short_answer: str
    self_check: SelfCheckResult
    used_template: bool = False
    invocations: tuple[ModelInvocation, ...] = ()
    error: NormalizedError | None = None

    @property
    def introduced_new_facts(self) -> bool:
        return self.self_check.unsupported_claims > 0


def _numbers_in(text: str) -> set[str]:
    """Cifras normalizadas presentes en un texto.

    Se quitan separadores de miles y espacios para que «1,250.00», «1 250.00» y
    «1250.00» sean el mismo número: el redactor formatea, y formatear no puede
    considerarse inventar.
    """
    found: set[str] = set()
    for match in _NUMBER.finditer(text):
        raw = match.group(0).replace(" ", "").replace(",", "")
        normalized = raw.rstrip(".").lstrip("0") or "0"
        # `814.00` y `814` son el mismo importe.
        if "." in normalized:
            normalized = normalized.rstrip("0").rstrip(".") or "0"
        found.add(normalized)
    return found


def _supported_numbers(facts: VerifiedFacts) -> set[str]:
    """Cifras que los hechos aceptados permiten mencionar."""
    supported: set[str] = set()
    for fact in facts.accepted():
        supported |= _numbers_in(fact.claim)
        value = fact.value
        if value.money is not None:
            units, cents = divmod(abs(value.money.amount_minor), 100)
            supported.add(str(units))
            supported.add(f"{units}.{cents:02d}".rstrip("0").rstrip(".") or "0")
            supported.add(str(value.money.amount_minor))
        if value.number is not None:
            supported.add(str(value.number).rstrip("0").rstrip(".") or "0")
        if value.date is not None:
            supported |= _numbers_in(value.date.isoformat())
        for item in value.items or []:
            supported |= _numbers_in(item)
        if value.text:
            supported |= _numbers_in(value.text)
    return supported


@dataclass
class Writer:
    """Redactor ciudadano. Su universo es el snapshot que recibe.

    El constructor acepta un gateway de modelo y nada más. No hay parámetro para
    un retriever ni para un executor, y ese es el punto.
    """

    gateway: ModelGateway
    prompt: Prompt | None = None
    alias: str = "structured_small"
    is_mock: bool = True
    deadline_ms: int = 6_000

    def __post_init__(self) -> None:
        if self.prompt is None:
            self.prompt = load_prompt("writer", "v1")
        forbidden = {"retriever", "tool_executor", "executor", "repository"}
        present = forbidden & set(vars(self))
        if present:  # pragma: no cover - defensa contra una regresión futura
            raise TypeError(
                f"el redactor no puede recibir {sorted(present)}: solo habla de los "
                f"VerifiedFacts que se le entregan (`DIE-F1-094`)"
            )

    async def write(
        self,
        facts: VerifiedFacts,
        context: ModelCallContext,
        *,
        channel: Channel = Channel.WEB,
        profile: Profile | None = None,
        warnings: Annotated[tuple[str, ...], Field(max_length=50)] = (),
        next_action: str | None = None,
    ) -> WritingOutcome:
        """Redacta la respuesta y verifica que no haya introducido hechos."""
        from nexo_orchestration.ports.model import ChatRequest, ModelPortError

        resolved_profile = profile or Profile()
        template = self.render_template(
            facts, channel=channel, warnings=warnings, next_action=next_action
        )
        if any(warning.startswith("[salud-seguridad]") for warning in warnings):
            return self._from_template(template, facts, channel, error=None)

        assert self.prompt is not None
        chat = ChatRequest(
            purpose=PURPOSE,
            task_kind=ModelTaskKind.DRAFTING,
            alias=self.alias,
            output_contract=OUTPUT_CONTRACT,
            prompt=self.prompt.render(
                audience=resolved_profile.audience.value,
                locale=resolved_profile.locale,
                channel=channel.value,
                facts=self._facts_block(facts),
                warnings="\n".join(f"- {warning}" for warning in warnings) or "(ninguna)",
                next_action=next_action or "(ninguna)",
            ),
            prompt_version=self.prompt.version,
            variables={"channel": channel.value},
            deadline_ms=self.deadline_ms,
        )

        try:
            outcome = await self.gateway.invoke(chat, context, DraftedAnswer)
        except ModelPortError as exc:
            return self._from_template(
                template,
                facts,
                channel,
                error=exc.error,
                invocations=tuple(exc.invocations),
            )

        drafted = outcome.value
        assert drafted is not None

        invented = self._invented_numbers(drafted.answer, facts)
        if invented:
            # `DIE-F1-098`: el modelo introdujo cifras que ningún hecho respalda.
            # No se corrige el texto ni se avisa y se entrega igual: se descarta
            # y se usa la plantilla, que no puede inventar nada.
            return self._from_template(
                template,
                facts,
                channel,
                error=NormalizedError.from_code(
                    ErrorCode.CONTRACT_INVALID,
                    f"la redacción introdujo {len(invented)} cifra(s) sin respaldo en "
                    f"los hechos verificados",
                ),
                invocations=tuple(outcome.invocations),
            )

        short = drafted.short_answer or self.render_template(
            facts, channel=Channel.WHATSAPP, warnings=warnings, next_action=next_action
        )
        return WritingOutcome(
            answer=drafted.answer,
            short_answer=short,
            self_check=SelfCheckResult(schema_valid=True, notes=["answer_grounded"]),
            invocations=tuple(outcome.invocations),
        )

    # -- self-check ---------------------------------------------------------

    def _invented_numbers(self, answer: str, facts: VerifiedFacts) -> set[str]:
        """Cifras del texto que ningún hecho aceptado respalda."""
        return _numbers_in(answer) - _supported_numbers(facts)

    # -- plantilla determinista (`DIE-F1-099`) ------------------------------

    def render_template(
        self,
        facts: VerifiedFacts,
        *,
        channel: Channel,
        warnings: tuple[str, ...] = (),
        next_action: str | None = None,
    ) -> str:
        """Respuesta sin modelo. Peor prosa, exactamente la misma información."""
        accepted = list(facts.accepted())
        lines: list[str] = []

        if not accepted:
            lines.append(
                "No encontré documentación vigente que respalde una respuesta, así que "
                "prefiero no afirmar nada. Puedes confirmarlo directamente en la dependencia."
            )
        else:
            requirements = [f for f in accepted if f.category is FactCategory.REQUIREMENT]
            costs = [f for f in accepted if f.category is FactCategory.COST]
            rest = [f for f in accepted if f not in requirements and f not in costs]

            if requirements:
                lines.append("Necesitas:")
                lines.extend(f"- {fact.claim}" for fact in requirements)
            if costs:
                lines.append("Costos:")
                lines.extend(f"- {self._cost_line(fact)}" for fact in costs)
            if rest:
                lines.append("Además:")
                lines.extend(f"- {fact.claim}" for fact in rest)

        if self.is_mock:
            # `DIE-F1-096`: la naturaleza mock se declara siempre.
            lines.append(
                "Aviso: esta respuesta usa datos de demostración y no sustituye al trámite oficial."
            )
        lines.extend(f"Aviso: {warning}" for warning in warnings)
        if next_action:
            lines.append(f"Siguiente paso: {next_action}")

        sources = sorted(
            {
                citation.source_id
                for fact in facts.facts
                if fact.verification is VerificationStatus.ACCEPTED
                for citation in fact.citations
                if citation.is_active
            }
        )
        if sources:
            lines.append(f"Fuentes: {', '.join(sources)}")

        limit = 1200 if channel is Channel.WHATSAPP else 20000
        return "\n".join(lines)[:limit]

    @staticmethod
    def _cost_line(fact: VerifiedFact) -> str:
        """El importe se añade solo si el claim no lo dice ya.

        Sin esta comprobación salía «cuesta 814.00 MXN. — 814.00 MXN»: el claim
        de un hecho de costo casi siempre menciona la cifra, y repetirla hace
        que la respuesta parezca generada por una plantilla, que es justo lo que
        es y justo lo que no debe notarse.
        """
        from nexo_a2ui import format_money

        money = fact.value.money
        if money is None:
            return fact.claim
        formatted = format_money(money)
        if _numbers_in(formatted) <= _numbers_in(fact.claim):
            return fact.claim
        return f"{fact.claim} — {formatted}"

    def _from_template(
        self,
        template: str,
        facts: VerifiedFacts,
        channel: Channel,
        *,
        error: NormalizedError | None,
        invocations: tuple[ModelInvocation, ...] = (),
    ) -> WritingOutcome:
        return WritingOutcome(
            answer=template,
            short_answer=self.render_template(facts, channel=Channel.WHATSAPP),
            self_check=SelfCheckResult(
                schema_valid=True,
                unsupported_claims=1 if error is not None else 0,
                notes=["deterministic_template"],
            ),
            used_template=True,
            invocations=invocations,
            error=error,
        )

    # -- prompt --------------------------------------------------------------

    def _facts_block(self, facts: VerifiedFacts) -> str:
        """Los hechos tal como se le muestran al modelo.

        Se muestran **solo los aceptados**. Enseñarle los rechazados le daría
        material para «matizar» algo que el verificador ya descartó.
        """
        lines: list[str] = []
        for fact in facts.accepted():
            citations = ", ".join(citation.fragment_id for citation in fact.citations)
            suffix = f" [{citations}]" if citations else ""
            lines.append(f"- ({fact.category.value}) {fact.claim}{suffix}")
        return "\n".join(lines) or "(no hay hechos verificados)"
