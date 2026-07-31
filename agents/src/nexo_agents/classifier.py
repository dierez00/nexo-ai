"""Clasificador de solicitudes (F1.4).

Es el primer agente del run y el más acotado: convierte un mensaje en lenguaje
natural en una `Classification` tipada, y no hace nada más. No consulta
documentación, no invoca tools y no redacta respuesta (`DIE-F1-033`). No es una
regla que el agente cumpla por buena voluntad: no recibe ni un `RetrieverPort`
ni un `ToolExecutorPort` en su constructor, así que no tiene con qué.

**El fallback determinista es la pieza que hace demostrable el MVP**
(`DIE-F1-034`). Cuando el modelo devuelve algo que no cumple el contrato, o el
proveedor no está, los casos oficiales siguen clasificando por coincidencia de
palabras clave declaradas en cada `domain.yaml`. Un MVP que solo funciona
cuando el proveedor responde no se puede enseñar.

El fallback no pretende ser bueno: pretende ser *previsible*. Marca su propia
confianza baja y deja constancia en el `SelfCheckResult` de que se usó.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from nexo_contracts import (
    Classification,
    DetectedIntent,
    Domain,
    ErrorCode,
    ModelTaskKind,
    NormalizedError,
    OperationalUrgency,
    RunRequest,
    SelfCheckResult,
)
from nexo_contracts.model_gateway import ModelInvocation

from .domain_manifest import DomainManifest
from .prompts import Prompt, load_prompt

if TYPE_CHECKING:  # pragma: no cover - solo para tipos
    from nexo_orchestration.models import ModelCallContext, ModelGateway

PURPOSE = "classify_request"
OUTPUT_CONTRACT = "classification"

# Confianza que se asigna a una clasificación producida por el fallback. Es
# deliberadamente baja: significa «esto coincidió por palabras, no porque nadie
# lo haya entendido», y el navegador debe tratarla como tal.
FALLBACK_CONFIDENCE = 0.45


@dataclass(frozen=True)
class ClassificationResult:
    """Salida del clasificador con todo lo que el grafo necesita registrar."""

    classification: Classification
    self_check: SelfCheckResult
    invocations: tuple[ModelInvocation, ...] = ()
    used_fallback: bool = False
    error: NormalizedError | None = None

    @property
    def domain(self) -> Domain | None:
        return self.classification.primary_domain


@dataclass
class Classifier:
    """Clasifica una solicitud contra el catálogo cerrado de intenciones.

    `manifests` es la allowlist: una intención que no esté declarada en ningún
    `domain.yaml` hace inválida la salida del modelo y dispara el fallback. Es
    lo que impide que el modelo invente un trámite que nadie sabe atender.
    """

    gateway: ModelGateway
    manifests: dict[Domain, DomainManifest]
    prompt: Prompt = field(default_factory=lambda: load_prompt("classifier", "v1"))
    alias: str = "structured_small"

    def __post_init__(self) -> None:
        self._by_slug: dict[str, tuple[Domain, str]] = {}
        for domain, manifest in self.manifests.items():
            for intent in manifest.intents:
                self._by_slug[intent.slug] = (domain, intent.title)

    # -- catálogo -----------------------------------------------------------

    def catalog_text(self) -> str:
        """Catálogo de intenciones tal como se le muestra al modelo."""
        lines: list[str] = []
        for domain in sorted(self.manifests, key=lambda item: item.value):
            manifest = self.manifests[domain]
            lines.append(f"### {manifest.title} (`{domain.value}`)")
            for intent in manifest.intents:
                description = intent.description.strip().replace("\n", " ")
                lines.append(f"- `{intent.slug}` — {intent.title}. {description}")
            lines.append("")
        return "\n".join(lines).strip()

    def known_slugs(self) -> frozenset[str]:
        return frozenset(self._by_slug)

    # -- clasificación ------------------------------------------------------

    async def classify(
        self, request: RunRequest, context: ModelCallContext
    ) -> ClassificationResult:
        """Clasifica la solicitud, con fallback determinista si el modelo falla."""
        from nexo_orchestration.ports.model import ChatRequest, ModelPortError

        chat = ChatRequest(
            purpose=PURPOSE,
            task_kind=ModelTaskKind.CLASSIFICATION,
            alias=self.alias,
            output_contract=OUTPUT_CONTRACT,
            prompt=self.prompt.render(
                intents_catalog=self.catalog_text(),
                channel=request.channel.value,
                audience=request.profile.audience.value,
                user_message=request.user_message,
            ),
            prompt_version=self.prompt.version,
            variables={"channel": request.channel.value},
            deadline_ms=3000,
        )

        try:
            outcome = await self.gateway.invoke(chat, context, Classification)
        except ModelPortError as exc:
            return self._fallback(request, invocations=(), error=exc.error)

        classification = outcome.value
        assert classification is not None  # `invoke` con contrato o devuelve valor o lanza

        unknown = self._unknown_intents(classification)
        if unknown:
            # El modelo cumplió el schema pero inventó un trámite. Es un fallo
            # de contenido, no de forma, y el schema no puede atraparlo: los
            # slugs válidos viven en la configuración, no en el tipo.
            return self._fallback(
                request,
                invocations=tuple(outcome.invocations),
                error=NormalizedError.from_code(
                    ErrorCode.MODEL_OUTPUT_INVALID,
                    f"la clasificación propone intenciones no declaradas: {sorted(unknown)}",
                ),
            )

        return ClassificationResult(
            classification=classification,
            self_check=self._self_check(classification),
            invocations=tuple(outcome.invocations),
        )

    def _unknown_intents(self, classification: Classification) -> set[str]:
        """Intenciones fuera del catálogo, o asignadas al dominio equivocado."""
        unknown: set[str] = set()
        for intent in classification.intents:
            declared = self._by_slug.get(intent.intent)
            if declared is None or declared[0] is not intent.domain:
                unknown.add(intent.intent)
        return unknown

    # -- self-check (`DIE-F1-036`) -----------------------------------------

    def _self_check(self, classification: Classification) -> SelfCheckResult:
        """Verifica schema, dominio permitido y ausencia de acciones.

        `forbidden_tool_requests` es estructuralmente cero: el contrato de
        `Classification` no tiene dónde poner una tool. Se declara igual para
        que el invariante quede escrito y para que añadir un campo de tools en
        el futuro rompa una prueba en vez de pasar inadvertido.
        """
        out_of_scope = len(self._unknown_intents(classification))
        notes: list[str] = []
        if classification.is_ambiguous:
            notes.append("ambiguity_declared")
        if classification.is_out_of_scope:
            notes.append("out_of_scope")
        return SelfCheckResult(
            schema_valid=True,
            unsupported_claims=0,
            out_of_scope_sources=out_of_scope,
            forbidden_tool_requests=0,
            notes=notes,
        )

    # -- fallback determinista (`DIE-F1-034`) -------------------------------

    def _fallback(
        self,
        request: RunRequest,
        *,
        invocations: tuple[ModelInvocation, ...],
        error: NormalizedError | None,
    ) -> ClassificationResult:
        classification = classify_by_keywords(request.user_message, self.manifests)
        self_check = self._self_check(classification)
        return ClassificationResult(
            classification=classification,
            self_check=self_check.model_copy(
                update={"notes": [*self_check.notes, "deterministic_fallback"]}
            ),
            invocations=invocations,
            used_fallback=True,
            error=error,
        )


def classify_by_keywords(message: str, manifests: dict[Domain, DomainManifest]) -> Classification:
    """Clasificación determinista por palabras clave declaradas (`DIE-F1-034`).

    Recorre las `keywords` de cada intención de cada `domain.yaml` y devuelve
    todas las que coinciden, ordenadas por número de coincidencias. Las
    intenciones **no se fusionan**: si el mensaje dispara `renovar_licencia` y
    `consultar_adeudo`, devuelve las dos, igual que haría el modelo.

    Sin modelo no hay forma de detectar ambigüedad ni de extraer entidades, así
    que la clasificación resultante es más pobre a propósito: baja confianza,
    sin entidades y sin ubicación. Lo que garantiza es que los casos oficiales
    se resuelvan sin proveedor.
    """
    from .keywords import normalize_for_match

    haystack = normalize_for_match(message)
    scored: list[tuple[int, int, DetectedIntent]] = []

    for domain in sorted(manifests, key=lambda item: item.value):
        for order, intent in enumerate(manifests[domain].intents):
            hits = sum(1 for keyword in intent.keywords if normalize_for_match(keyword) in haystack)
            if hits:
                scored.append(
                    (
                        hits,
                        -order,
                        DetectedIntent(
                            intent=intent.slug,
                            domain=domain,
                            confidence=FALLBACK_CONFIDENCE,
                            rationale="coincidencia determinista de palabras clave",
                        ),
                    )
                )

    if not scored:
        return Classification(
            entities={},
            confidence=0.0,
            is_out_of_scope=True,
        )

    # Más coincidencias primero; a igualdad, el orden declarado en el manifiesto.
    scored.sort(key=lambda item: (-item[0], -item[1]))
    return Classification(
        intents=[intent for _, _, intent in scored],
        urgency=OperationalUrgency.ROUTINE,
        entities={},
        confidence=FALLBACK_CONFIDENCE,
    )
