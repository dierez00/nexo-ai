"""Navegador de dominio (F1.5).

Recupera evidencia de su namespace, extrae hechos candidatos con citaciones y
propone tools de lectura. No ejecuta ninguna, no verifica nada y no redacta la
respuesta: eso es del executor, del verificador y del redactor.

La pieza que sostiene el gate de grounding está aquí, y no en el prompt: **el
modelo no construye las citaciones, las construye el navegador**. Al modelo se
le muestran fragmentos con su identificador y solo puede referenciar esos
identificadores; cualquier hecho que apunte a un fragmento que no se recuperó se
descarta y se cuenta como `unsupported_claim`. Un modelo no puede inventar una
fuente que no vio, porque la citación no la escribe él.

Ese control existe además del prompt porque un prompt es una petición y esto es
una comprobación. Las dos hacen falta; solo una es verificable.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from nexo_contracts import (
    AgentName,
    CandidateFact,
    Classification,
    Deduction,
    DetectedIntent,
    Domain,
    FactCategory,
    FactOrigin,
    FactValue,
    ModelTaskKind,
    NexoModel,
    NormalizedError,
    ProposedToolCall,
    RetrievalFilters,
    RetrievalQuery,
    RetrievalResponse,
    RetrievalResult,
    RunRequest,
    SafePayload,
    SelfCheckResult,
    SourceCitation,
    SourceStatus,
    TaskStatus,
    ToolMode,
)
from nexo_contracts.ids import FragmentId
from nexo_contracts.model_gateway import ModelInvocation
from nexo_contracts.primitives import Confidence

from .domain_manifest import DomainManifest
from .health_safety import assess_health_message
from .prompts import Prompt, load_by_ref

if TYPE_CHECKING:  # pragma: no cover - solo para tipos
    from nexo_orchestration.models import ModelCallContext, ModelGateway
    from nexo_rag.ports import RetrieverPort

PURPOSE = "navigate_domain"
OUTPUT_CONTRACT = "fact_extraction"


class ExtractedFact(NexoModel):
    """Un hecho tal como lo propone el modelo, antes de resolver su citación.

    `fragment_ids` es la única forma que tiene el modelo de respaldar un claim:
    referencias a fragmentos que se le mostraron. No puede escribir una
    citación completa, ni una URL, ni un nombre de fuente.
    """

    claim: str = Field(max_length=1000)
    category: FactCategory
    value: FactValue
    fragment_ids: Annotated[list[FragmentId], Field(max_length=10)] = Field(default_factory=list)
    confidence: Confidence = 0.8


class ProposedTool(NexoModel):
    """Tool que el modelo sugiere invocar. El navegador la filtra y no la ejecuta."""

    name: str = Field(max_length=95)
    rationale: str = Field(default="", max_length=300)
    parameters: SafePayload = Field(default_factory=dict)


class FactExtraction(NexoModel):
    """Contrato de salida del navegador (interno del paquete de agentes).

    No se publica en `contracts/`: es un paso intermedio entre el retrieval y
    los `CandidateFact`, y publicarlo obligaría a versionarlo como si fuera una
    frontera entre equipos, que no lo es.
    """

    facts: Annotated[list[ExtractedFact], Field(max_length=50)] = Field(default_factory=list)
    proposed_tools: Annotated[list[ProposedTool], Field(max_length=10)] = Field(
        default_factory=list
    )
    missing_information: Annotated[list[str], Field(max_length=20)] = Field(default_factory=list)
    question: str | None = Field(
        default=None,
        max_length=500,
        description="Pregunta mínima, solo si sin ella el trámite sería incorrecto.",
    )


@dataclass(frozen=True)
class NavigationResult:
    """Salida del navegador, lista para el supervisor."""

    facts: tuple[CandidateFact, ...]
    citations: tuple[SourceCitation, ...]
    proposed_tools: tuple[ProposedToolCall, ...]
    self_check: SelfCheckResult
    question: str | None = None
    warnings: tuple[str, ...] = ()
    invocations: tuple[ModelInvocation, ...] = ()
    status: TaskStatus = TaskStatus.SUCCEEDED
    error: NormalizedError | None = None


@dataclass
class DomainNavigator:
    """Navegador acotado a un dominio (`DIE-F1-040`).

    Los tres límites son de construcción, no de comportamiento: el manifiesto
    fija el namespace, la allowlist de fuentes y la de tools, y el navegador no
    tiene forma de ampliarlos. Pedir evidencia de otro dominio no es algo que
    «no deba hacer»: es algo que no puede expresar, porque la consulta lleva su
    `Domain` fijo.
    """

    domain: Domain
    manifest: DomainManifest
    gateway: ModelGateway
    retriever: RetrieverPort
    prompt: Prompt | None = None
    alias: str = "general"
    fact_id_prefix: str = "fact"

    def __post_init__(self) -> None:
        if self.manifest.domain is not self.domain:
            raise ValueError(
                f"el navegador de '{self.domain.value}' recibió el manifiesto de "
                f"'{self.manifest.domain.value}'"
            )
        if self.prompt is None:
            self.prompt = load_by_ref(self.manifest.prompt_ref)

    # -- recuperación -------------------------------------------------------

    async def retrieve(
        self, query: str, request: RunRequest, valid_at: date
    ) -> list[RetrievalResult]:
        """Evidencia del namespace, con la allowlist del manifiesto aplicada.

        `allowed_source_ids` se pasa siempre, aunque el retriever ya filtre por
        dominio: son dos allowlists distintas —la del namespace y la del
        manifiesto— y la segunda puede ser más estrecha que la primera.
        """
        response = await self.retriever.retrieve(
            RetrievalQuery(
                query=query,
                domain=self.domain,
                filters=RetrievalFilters(
                    institution_id=request.identity.institution_id,
                    status=[SourceStatus.ACTIVE],
                    valid_at=valid_at,
                    allowed_source_ids=list(self.manifest.allowed_sources),
                ),
                top_k=self.manifest.policies.retrieval_top_k,
            )
        )
        return list(response.results)

    # -- navegación ---------------------------------------------------------

    async def navigate(
        self,
        request: RunRequest,
        classification: Classification,
        context: ModelCallContext,
        *,
        valid_at: date,
        evidence: Sequence[RetrievalResult] | None = None,
    ) -> NavigationResult:
        """Extrae hechos candidatos y propone tools de lectura.

        `evidence` permite que el grafo recupere en un nodo aparte (`retrieve`) y
        navegue en otro (`navigate`), que es como los nombra `DIE-F1-083`. Sin
        él, el navegador recupera por su cuenta: sigue siendo usable suelto.
        """
        from nexo_orchestration.ports.model import ChatRequest, ModelPortError
        from nexo_rag.retrieval import assess

        intents = [i for i in classification.intents if i.domain is self.domain]
        results = (
            list(evidence)
            if evidence is not None
            else await self.retrieve(self.query_for(request, intents), request, valid_at)
        )

        warnings: list[str] = []
        if self.domain is Domain.SALUD:
            safety = assess_health_message(request.user_message)
            if safety.blocked_clinical_request:
                warning = safety.warning or "Solicitud clínica fuera del alcance administrativo."
                fact = CandidateFact(
                    fact_id=f"{self.fact_id_prefix}_sal_safe",
                    claim=warning.removeprefix("[salud-seguridad] "),
                    value=FactValue(text="orientacion_administrativa_sin_consejo_clinico"),
                    category=FactCategory.CONTEXT,
                    domain=Domain.SALUD,
                    origin=FactOrigin.DEDUCTION,
                    confidence=1.0,
                    deduction=Deduction(
                        value=FactValue(text="orientacion_administrativa_sin_consejo_clinico"),
                        source=FactOrigin.DEDUCTION,
                        confidence=1.0,
                        confirmed_by_user=False,
                        write_eligible=False,
                        rationale="Límite de alcance aplicado por una regla determinista.",
                    ),
                )
                return NavigationResult(
                    facts=(fact,),
                    citations=(),
                    proposed_tools=(),
                    self_check=SelfCheckResult(
                        schema_valid=True,
                        notes=["health_clinical_request_blocked"],
                    ),
                    warnings=(warning,),
                    status=TaskStatus.PARTIAL,
                )

        assessment = assess(_as_response(results))
        if assessment.warning:
            warnings.append(assessment.warning)

        # `DIE-F1-026`: la señal de injection se registra y el fragmento se
        # entrega como dato. Nada de lo que diga cambia la allowlist ni el plan.
        flagged = [r for r in results if r.injection_signals]
        if flagged:
            warnings.append(
                f"{len(flagged)} fragmento(s) recuperado(s) contienen contenido anómalo y "
                f"no se usan como respaldo"
            )

        usable = [r for r in results if not r.injection_signals]
        if not usable:
            return NavigationResult(
                facts=(),
                citations=(),
                proposed_tools=(),
                self_check=SelfCheckResult(schema_valid=True),
                question=None,
                warnings=tuple(warnings),
                status=TaskStatus.PARTIAL,
            )

        chat = ChatRequest(
            purpose=PURPOSE,
            task_kind=ModelTaskKind.NAVIGATION,
            alias=self.alias,
            output_contract=OUTPUT_CONTRACT,
            prompt=self._render(request, intents, usable),
            prompt_version=self.prompt.version if self.prompt else "v1",
            variables={"domain": self.domain.value},
            deadline_ms=self.manifest.policies.navigator_deadline_ms,
        )

        try:
            outcome = await self.gateway.invoke(chat, context, FactExtraction)
        except ModelPortError as exc:
            return NavigationResult(
                facts=(),
                citations=(),
                proposed_tools=(),
                self_check=SelfCheckResult(schema_valid=False),
                warnings=tuple(warnings),
                invocations=tuple(exc.invocations),
                status=TaskStatus.FAILED,
                error=exc.error,
            )

        extraction = outcome.value
        assert extraction is not None

        by_fragment = {result.fragment_id: result for result in usable}
        facts, unsupported = self._to_candidate_facts(extraction, by_fragment)
        tools, forbidden = self._filter_tools(extraction)

        if unsupported:
            warnings.append(
                f"{unsupported} afirmación(es) del modelo no citaban evidencia recuperada "
                f"y se descartaron"
            )

        return NavigationResult(
            facts=tuple(facts),
            citations=tuple(_unique_citations(facts)),
            proposed_tools=tuple(tools),
            self_check=SelfCheckResult(
                schema_valid=True,
                unsupported_claims=unsupported,
                out_of_scope_sources=0,
                forbidden_tool_requests=forbidden,
                notes=["evidence_" + assessment.verdict.value],
            ),
            question=self._question(extraction, classification),
            warnings=tuple(warnings),
            invocations=tuple(outcome.invocations),
            status=TaskStatus.SUCCEEDED if facts else TaskStatus.PARTIAL,
        )

    # -- conversión ---------------------------------------------------------

    def _to_candidate_facts(
        self, extraction: FactExtraction, by_fragment: dict[str, RetrievalResult]
    ) -> tuple[list[CandidateFact], int]:
        """Convierte lo extraído en hechos candidatos con citación resuelta.

        Un hecho que referencia un fragmento que no se recuperó se **descarta**,
        no se degrada: es literalmente una fuente inventada. Los hechos no
        críticos sin ninguna citación sí se conservan, marcados como deducción
        del modelo, porque orientar sin citar es legítimo mientras no se afirme
        un requisito, un costo ni una vigencia.
        """
        facts: list[CandidateFact] = []
        unsupported = 0

        for ordinal, extracted in enumerate(extraction.facts, start=1):
            citations = [
                by_fragment[fragment].citation
                for fragment in extracted.fragment_ids
                if fragment in by_fragment
            ]
            hallucinated = [f for f in extracted.fragment_ids if f not in by_fragment]

            if hallucinated:
                unsupported += 1
                continue

            is_critical = extracted.category in _CRITICAL
            if is_critical and not citations:
                unsupported += 1
                continue

            facts.append(
                CandidateFact(
                    fact_id=f"{self.fact_id_prefix}_{self.domain.value[:3]}{ordinal:04d}",
                    claim=extracted.claim,
                    value=extracted.value,
                    category=extracted.category,
                    domain=self.domain,
                    origin=FactOrigin.RAG if citations else FactOrigin.DEDUCTION,
                    confidence=extracted.confidence,
                    citations=citations,
                    deduction=(
                        None
                        if citations
                        else Deduction(
                            value=extracted.value,
                            source=FactOrigin.DEDUCTION,
                            confidence=extracted.confidence,
                            confirmed_by_user=False,
                            write_eligible=False,
                            rationale=(
                                "Orientación no crítica inferida por el navegador sin "
                                "evidencia documental."
                            ),
                        )
                    ),
                )
            )
        return facts, unsupported

    def _filter_tools(self, extraction: FactExtraction) -> tuple[list[ProposedToolCall], int]:
        """Filtra las tools propuestas contra la allowlist del manifiesto.

        Todas se proponen en modo lectura. Una escritura solo puede nacer de una
        `ActionRequest` confirmada que ejecuta el agente transaccional, y el
        contrato de `AgentResult` rechaza que cualquier otro agente proponga una
        (`DIE-F1-042`).
        """
        allowed = set(self.manifest.allowed_tools)
        writes = set(self.manifest.write_tools())
        tools: list[ProposedToolCall] = []
        forbidden = 0

        for proposed in extraction.proposed_tools:
            if proposed.name not in allowed or proposed.name in writes:
                forbidden += 1
                continue
            tools.append(
                ProposedToolCall(
                    name=proposed.name,
                    mode=ToolMode.READ,
                    rationale=proposed.rationale,
                    parameters=proposed.parameters,
                )
            )
        return tools, forbidden

    def _question(self, extraction: FactExtraction, classification: Classification) -> str | None:
        """Pregunta mínima, si el presupuesto del dominio la permite (`DIE-F1-044`).

        Se pregunta solo cuando falta un dato obligatorio o hay ambigüedad
        material. Preguntar «por si acaso» convierte un trámite de un paso en
        una conversación de cinco.
        """
        if self.manifest.policies.max_questions <= 0:
            return None
        if extraction.question:
            return extraction.question
        if classification.is_ambiguous and classification.ambiguity_reason:
            return classification.ambiguity_reason
        return None

    # -- prompt -------------------------------------------------------------

    def query_for(self, request: RunRequest, intents: Sequence[DetectedIntent]) -> str:
        """Consulta de retrieval: el mensaje más los títulos de las intenciones.

        Añadir los títulos ancla el vocabulario administrativo que la persona no
        usa: quien pregunta «si debo algo» no escribe «adeudo vehicular».
        """
        catalog_terms = [
            " ".join((declared.title, declared.description))
            for intent in intents
            if (declared := self.manifest.intent(intent.intent)) is not None
        ]
        return " ".join([request.user_message, *catalog_terms]).strip()

    def _render(
        self,
        request: RunRequest,
        intents: Sequence[DetectedIntent],
        results: list[RetrievalResult],
    ) -> str:
        assert self.prompt is not None
        fragments = "\n\n".join(
            f"### {result.fragment_id}\n"
            f"Fuente: {result.source_id} — {result.title}\n\n{result.text}"
            for result in results
        )
        slugs = ", ".join(intent.intent for intent in intents) or "(ninguna)"
        return self.prompt.render(
            domain=self.manifest.title,
            intents=slugs,
            allowed_tools=", ".join(self.manifest.allowed_tools) or "(ninguna)",
            user_message=request.user_message,
            fragments=fragments,
        )


_CRITICAL = frozenset(
    {
        FactCategory.REQUIREMENT,
        FactCategory.COST,
        FactCategory.LOCATION,
        FactCategory.VALIDITY,
        FactCategory.DEPENDENCY,
        FactCategory.ACTION_RESULT,
    }
)


def _unique_citations(facts: list[CandidateFact]) -> list[SourceCitation]:
    seen: set[tuple[str, str]] = set()
    unique: list[SourceCitation] = []
    for fact in facts:
        for citation in fact.citations:
            key = (citation.source_id, citation.fragment_id)
            if key not in seen:
                seen.add(key)
                unique.append(citation)
    return unique


def _as_response(results: list[RetrievalResult]) -> RetrievalResponse:
    """Envuelve resultados sueltos para poder evaluarlos con `assess`."""
    return RetrievalResponse(results=results, corpus_version="", filtered_count=0)


def navigator_agent_name() -> AgentName:
    return AgentName.DOMAIN_NAVIGATOR
