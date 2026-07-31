"""Ejemplos canónicos válidos e inválidos de cada contrato (`DIE-F0-018`).

Los ejemplos **válidos** se construyen como instancias reales de los modelos: no
pueden desincronizarse del contrato porque, si dejaran de validar, este módulo
dejaría de importar. Los **inválidos** se declaran como payloads crudos junto a
la regla que debe rechazarlos, porque su valor está justamente en no ser
construibles.

Todo el contenido es sintético y sin PII: nombres, folios, placas y direcciones
son de demostración (`DIE-F0-029`).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any, NamedTuple

from .a2ui import (
    A2UIComponent,
    A2UIMessage,
    A2UISurface,
    A2UIValidationResult,
    CatalogDescriptor,
    ChannelFallback,
    ComponentDescriptor,
    CreateSurface,
    UpdateComponents,
    UpdateDataModel,
)
from .base import NexoModel
from .classification import Classification, DetectedIntent
from .enums import (
    A2UIValidationOutcome,
    ActionStatus,
    ActorType,
    AgentName,
    Audience,
    Channel,
    ContradictionSeverity,
    ContradictionStatus,
    CorpusStatus,
    Domain,
    ErrorCode,
    EventStatus,
    EventType,
    FactCategory,
    FactOrigin,
    IngestionOutcome,
    IntegrationState,
    ModelDecisionReason,
    ModelHealth,
    ModelTaskKind,
    OperationalUrgency,
    Outcome,
    RetrievalMode,
    RiskLevel,
    RunStatus,
    SourceStatus,
    TaskStatus,
    ToolCallStatus,
    ToolMode,
    VerificationStatus,
)
from .errors import NormalizedError
from .estimation import Estimate, EstimateStep
from .evaluation import (
    DeterministicEvaluationResult,
    EvaluationReport,
    JudgeRequest,
    JudgeResult,
    JudgeScores,
    SelfCheckResult,
)
from .events import EventActor, EventSequence, RunEvent
from .execution import (
    ActionRequest,
    ActionResult,
    AgentResult,
    AgentTask,
    Budgets,
    Identity,
    Profile,
    RunMetrics,
    RunRequest,
    RunResult,
    RunSnapshot,
    RunState,
)
from .facts import (
    CandidateFact,
    Contradiction,
    Deduction,
    FactValue,
    SourceCitation,
    VerifiedFact,
    VerifiedFacts,
)
from .model_gateway import (
    ModelCandidate,
    ModelCapabilities,
    ModelDecision,
    ModelInvocation,
    ModelPolicy,
    ModelTask,
)
from .observability import CatalogEntityTelemetry
from .primitives import Money, ValidityWindow
from .rag import (
    Chunk,
    CorpusVersion,
    Document,
    DocumentVersion,
    IngestionResult,
    RetrievalFilters,
    RetrievalQuery,
    RetrievalResponse,
    RetrievalResult,
    Source,
)
from .skills import SkillBudgets, SkillManifest, SkillStep
from .tools import (
    Approval,
    ControlledTestResult,
    IntegrationDraft,
    MapperValidation,
    PublishedToolVersion,
    ToolCall,
    ToolConfirmation,
    ToolError,
    ToolMetadata,
    ToolPermissionContext,
    ToolResult,
)

# Reloj congelado: los ejemplos deben producir bytes idénticos en cada
# regeneración para que un diff signifique un cambio de contrato real.
FIXED_NOW = datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)
FIXED_DATE = date(2026, 7, 30)
DEMO_CORPUS_VERSION = "vehiculos-demo-2026-07-20"
CITIZEN_CATALOG = "urn:nexo-ia:a2ui:catalog:citizen:v1"
CHECKSUM = "sha256:" + "0" * 64

# --------------------------------------------------------------------------
# Piezas compartidas del recorrido CAP-VEH-01 (renovar licencia + adeudo)
# --------------------------------------------------------------------------

LICENSE_CITATION = SourceCitation(
    source_id="src_licencias_v3",
    fragment_id="frag_12",
    corpus_version=DEMO_CORPUS_VERSION,
    source_version="3",
    valid_from=date(2026, 1, 1),
    is_active=True,
    char_start=0,
    char_end=180,
)

COST_FACT = VerifiedFact(
    fact_id="fact_cost_01",
    claim="El costo de renovación de demostración es de 1,250.00 MXN.",
    value=FactValue(money=Money(amount_minor=125000, currency="MXN")),
    category=FactCategory.COST,
    domain=Domain.VEHICULOS,
    verification=VerificationStatus.ACCEPTED,
    reason="citation_supports_claim",
    confidence=0.97,
    citations=[LICENSE_CITATION],
    write_eligible=True,
)

REQUIREMENT_FACT = VerifiedFact(
    fact_id="fact_req_01",
    claim="Se requiere identificación oficial vigente.",
    value=FactValue(items=["Identificación oficial vigente"]),
    category=FactCategory.REQUIREMENT,
    domain=Domain.VEHICULOS,
    verification=VerificationStatus.ACCEPTED,
    reason="citation_supports_claim",
    confidence=0.95,
    citations=[LICENSE_CITATION],
)

VERIFIED_FACTS = VerifiedFacts(
    snapshot_id="snapshot_cap_veh_01",
    created_at=FIXED_NOW,
    facts=(REQUIREMENT_FACT, COST_FACT),
)

IDENTITY = Identity(
    user_id="usr_demo",
    institution_id="inst_demo",
    roles=["citizen"],
    permissions=["domain:vehiculos:read", "appointment:create"],
)

RUN_REQUEST = RunRequest(
    run_id="run_01JNE8ZP",
    trace_id="trace_01JNE8ZP",
    conversation_id="conv_01",
    user_message="Quiero renovar mi licencia y saber si debo algo",
    channel=Channel.WEB,
    identity=IDENTITY,
    profile=Profile(audience=Audience.CITIZEN, locale="es-MX"),
    budgets=Budgets(deadline_ms=20000, max_cost_usd=0.20),
    received_at=FIXED_NOW,
)

RESERVE_ACTION = ActionRequest(
    action_id="act_reserve_01",
    run_id="run_01JNE8ZP",
    tool_name="vehiculos.reservar_cita",
    input_schema_ref="contracts://tools/vehiculos.reservar_cita.input.v1",
    tool_version="1.0.0",
    expected_version=1,
    parameters={"slot_id": "slot_101"},
    requires_confirmation=True,
    required_permission="appointment:create",
    supporting_fact_ids=["fact_cost_01"],
)

RESERVE_TOOL = ToolMetadata(
    name="vehiculos.reservar_cita",
    version="1.0.0",
    domain=Domain.VEHICULOS,
    mode=ToolMode.WRITE,
    risk=RiskLevel.MEDIUM,
    allowed_roles=["citizen", "operator"],
    requires_confirmation=True,
    requires_idempotency_key=True,
    timeout_ms=5000,
    max_attempts=1,
    input_schema_ref="contracts://tools/vehiculos.reservar_cita.input.v1",
    output_schema_ref="contracts://tools/vehiculos.reservar_cita.output.v1",
    description="Reserva un slot autorizado. Exige confirmación e idempotencia.",
)

RESERVE_CALL = ToolCall(
    tool_call_id="tc_01",
    name="vehiculos.reservar_cita",
    version="1.0.0",
    run_id="run_01JNE8ZP",
    trace_id="trace_01JNE8ZP",
    context=ToolPermissionContext(
        user_id="usr_demo",
        institution_id="inst_demo",
        roles=["citizen"],
        permissions=["appointment:create"],
    ),
    parameters={"slot_id": "slot_101"},
    deadline_ms=5000,
    action_id="act_reserve_01",
    idempotency_key="824a2b5c-1389-4ef5-a346-b00270fd1b42",
    confirmed=True,
    mode=ToolMode.WRITE,
)

RESERVE_RESULT = ToolResult(
    tool_call_id="tc_01",
    name="vehiculos.reservar_cita",
    status=ToolCallStatus.SUCCEEDED,
    data={"appointment_id": "apt_01JNE9"},
    confirmation=ToolConfirmation(
        identifier="NEXO-MOCK-2026-000101",
        identifier_kind="folio",
        is_mock=True,
        issued_at=FIXED_NOW,
    ),
    provider="mock",
    duration_ms=84,
    is_mock=True,
)

SURFACE = A2UISurface(
    surface_id="surf_licencia",
    catalog_id=CITIZEN_CATALOG,
    channel=Channel.WEB,
    messages=[
        A2UIMessage(
            create_surface=CreateSurface(surface_id="surf_licencia", catalog_id=CITIZEN_CATALOG)
        ),
        A2UIMessage(
            update_data_model=UpdateDataModel(
                surface_id="surf_licencia",
                path="/",
                value={"title": "Renovación de licencia", "total": "1,250.00 MXN"},
            )
        ),
        A2UIMessage(
            update_components=UpdateComponents(
                surface_id="surf_licencia",
                components=[
                    A2UIComponent(id="root", component="Column", children=["title", "confirm"]),
                    A2UIComponent(
                        id="title", component="Text", properties={"text": {"path": "/title"}}
                    ),
                    A2UIComponent(
                        id="confirm",
                        component="Button",
                        properties={"label": "Confirmar cita"},
                        action_id="act_reserve_01",
                    ),
                ],
            )
        ),
    ],
    actions=[RESERVE_ACTION.to_a2ui_action(label="Confirmar cita")],
)

RUN_STATE = RunState(
    run_id="run_01JNE8ZP",
    trace_id="trace_01JNE8ZP",
    conversation_id="conv_01",
    status=RunStatus.WAITING_CONFIRMATION,
    request=RUN_REQUEST,
    created_at=FIXED_NOW,
    updated_at=FIXED_NOW,
    domain=Domain.VEHICULOS,
    verified_facts=VERIFIED_FACTS,
    pending_action=RESERVE_ACTION,
    surface=SURFACE,
    answer="Puedes renovar tu licencia presentando identificación oficial vigente.",
    metrics=RunMetrics(duration_ms=4200, total_cost_usd=0.012, model_invocation_count=2),
    event_cursor=7,
    completed_nodes=["start", "classify_fake"],
    policy_version="policies-2026-07-30",
)

MODEL_DECISION = ModelDecision(
    requested_alias="high_accuracy",
    selected_alias="high_accuracy_secondary",
    reason=ModelDecisionReason.PRIMARY_PROVIDER_DEGRADED,
    considered=[
        ModelCandidate(
            alias="high_accuracy",
            capabilities=ModelCapabilities(
                supports_structured_output=True,
                max_context_tokens=200_000,
                max_output_tokens=8192,
                cost_per_1k_input_usd=0.003,
                cost_per_1k_output_usd=0.015,
            ),
            health=ModelHealth.DEGRADED,
            score=0.4,
            rejected_reason="provider_degraded",
        ),
    ],
    policy_version="policies-2026-07-30",
    max_cost_usd=0.08,
)

RUN_EVENT = RunEvent(
    event_id="evt_01",
    trace_id="trace_01JNE8ZP",
    run_id="run_01JNE8ZP",
    sequence=14,
    type=EventType.TOOL_COMPLETED,
    timestamp=FIXED_NOW,
    actor=EventActor(type=ActorType.TOOL, name="vehiculos.consultar_adeudo"),
    status=EventStatus.SUCCEEDED,
    correlation_id="trace_01JNE8ZP",
    duration_ms=320,
    data={"tool_call_id": "tc_01", "is_mock": True},
    policy_version="policies-2026-07-30",
)

# --------------------------------------------------------------------------
# Recorrido CAP-EMP-01 (abrir una taquería): estimación con DAG de permisos
# --------------------------------------------------------------------------

BUSINESS_ESTIMATE = Estimate(
    domain=Domain.AYUNTAMIENTO_EMPRESAS,
    steps=[
        EstimateStep(
            step_id="uso_de_suelo",
            title="Constancia de uso de suelo",
            cost=Money(amount_minor=85000, currency="MXN"),
            duration_days=5,
            derived_from=["fact_cost_01"],
        ),
        EstimateStep(
            step_id="licencia_funcionamiento",
            title="Licencia de funcionamiento",
            depends_on=["uso_de_suelo"],
            cost=Money(amount_minor=140000, currency="MXN"),
            duration_days=10,
            missing_documents=["Contrato de arrendamiento"],
            derived_from=["fact_cost_01"],
        ),
    ],
    total_cost=Money(amount_minor=225000, currency="MXN"),
    derived_from=["fact_cost_01"],
)


def _valid_examples() -> dict[str, NexoModel]:
    """Un ejemplo canónico por contrato publicado."""
    return {
        # §5.1
        "run_request": RUN_REQUEST,
        "run_state": RUN_STATE,
        "run_result": RunResult.from_state(RUN_STATE, action_label="Confirmar cita"),
        "run_snapshot": RunSnapshot(state=RUN_STATE, events=[RUN_EVENT]),
        "catalog_entity_telemetry": CatalogEntityTelemetry(
            entity_id="tool:vehiculos.consultar_adeudo",
            state="healthy",
            window_started_at=FIXED_NOW,
            window_ended_at=FIXED_NOW,
            last_checked_at=FIXED_NOW,
        ),
        "agent_task": AgentTask(
            task_id="task_verify_01",
            run_id="run_01JNE8ZP",
            agent=AgentName.VERIFIER,
            objective="Validar requisitos, costos, ubicaciones y vigencia",
            input_refs=["fact_req_01", "fact_cost_01"],
            allowed_sources=["src_licencias_v3"],
            deadline_ms=6000,
            model_policy="high_accuracy",
        ),
        "agent_result": AgentResult(
            task_id="task_verify_01",
            agent=AgentName.VERIFIER,
            status=TaskStatus.SUCCEEDED,
            citations=[LICENSE_CITATION],
            self_check=SelfCheckResult(schema_valid=True),
            confidence=0.96,
        ),
        # El ejemplo canónico es el caso oficial `CAP-VEH-01`: dos intenciones
        # que deben conservarse separadas (`DIE-F1-032`).
        "classification": Classification(
            intents=[
                DetectedIntent(
                    intent="renovar_licencia",
                    domain=Domain.VEHICULOS,
                    confidence=0.94,
                    rationale="La persona dice explícitamente que quiere renovar.",
                ),
                DetectedIntent(
                    intent="consultar_adeudo",
                    domain=Domain.VEHICULOS,
                    confidence=0.88,
                    rationale=(
                        "«saber si debo algo» es una consulta de adeudo, no parte de la renovación."
                    ),
                ),
            ],
            location="Durango",
            audience=Audience.CITIZEN,
            urgency=OperationalUrgency.ROUTINE,
            entities={"tipo_licencia": "A"},
            missing_information=["numero_de_licencia"],
            confidence=0.91,
        ),
        "action_request": RESERVE_ACTION,
        "action_result": ActionResult(
            action_id="act_reserve_01",
            status=ActionStatus.SUCCEEDED,
            tool_call_id="tc_01",
            tool_result=RESERVE_RESULT,
        ),
        # §5.2
        "candidate_fact": CandidateFact(
            fact_id="fact_cost_01",
            claim="El costo de renovación de demostración es de 1,250.00 MXN.",
            value=FactValue(money=Money(amount_minor=125000, currency="MXN")),
            category=FactCategory.COST,
            domain=Domain.VEHICULOS,
            origin=FactOrigin.RAG,
            confidence=0.92,
            citations=[LICENSE_CITATION],
        ),
        "verified_fact": COST_FACT,
        "verified_facts": VERIFIED_FACTS,
        "source_citation": LICENSE_CITATION,
        "contradiction": Contradiction(
            contradiction_id="contra_01",
            fact_ids=["fact_cost_01", "fact_cost_02"],
            severity=ContradictionSeverity.CRITICAL,
            status=ContradictionStatus.RESOLVED,
            rule="newer_active_source_wins",
            explanation="Dos fuentes declaran costos distintos; prevalece la vigente.",
            conflicting_sources=["src_licencias_v3", "src_licencias_v2"],
            resolved_fact_id="fact_cost_01",
        ),
        "deduction": Deduction(
            value=FactValue(text="Durango"),
            source=FactOrigin.PROFILE,
            confidence=0.8,
            confirmed_by_user=True,
            write_eligible=True,
            rationale="El perfil declara Durango y la persona lo confirmó en el turno previo.",
        ),
        "estimate": BUSINESS_ESTIMATE,
        # §5.3
        "source": Source(
            source_id="src_licencias_v3",
            title="Renovación de licencia — versión demo 3",
            institution_id="inst_demo",
            domain=Domain.VEHICULOS,
            origin_url="https://example.invalid/demo/licencias",
            publisher="Dependencia de demostración",
            owner="equipo-nexo",
            license="Uso interno de demostración",
            status=SourceStatus.ACTIVE,
            validity=ValidityWindow(valid_from=date(2026, 1, 1)),
            verified_at=FIXED_NOW,
            is_synthetic=True,
        ),
        "document": Document(
            document_id="doc_licencias_01",
            source_id="src_licencias_v3",
            title="Requisitos de renovación",
            media_type="text/markdown",
            original_path="data/documents/vehiculos/licencias_v3.md",
        ),
        "document_version": DocumentVersion(
            document_id="doc_licencias_01",
            version="3",
            checksum=CHECKSUM,
            ingested_at=FIXED_NOW,
            is_active=True,
        ),
        "chunk": Chunk(
            chunk_id="chunk_0001",
            fragment_id="frag_12",
            document_id="doc_licencias_01",
            source_id="src_licencias_v3",
            domain=Domain.VEHICULOS,
            institution_id="inst_demo",
            document_version="3",
            ordinal=0,
            heading="Requisitos",
            text="Presentar identificación oficial vigente y comprobante de pago.",
            char_start=0,
            char_end=180,
            checksum=CHECKSUM,
            validity=ValidityWindow(valid_from=date(2026, 1, 1)),
            status=SourceStatus.ACTIVE,
            embedding_model="fake-embeddings",
            embedding_dimension=64,
        ),
        "corpus_version": CorpusVersion(
            corpus_version=DEMO_CORPUS_VERSION,
            domain=Domain.VEHICULOS,
            status=CorpusStatus.ACTIVE,
            created_at=FIXED_NOW,
            source_ids=["src_licencias_v3"],
            chunk_count=1,
        ),
        "retrieval_query": RetrievalQuery(
            query="requisitos vigentes para renovar licencia",
            domain=Domain.VEHICULOS,
            filters=RetrievalFilters(
                institution_id="inst_demo",
                status=[SourceStatus.ACTIVE],
                valid_at=FIXED_DATE,
            ),
            top_k=5,
            retrieval_mode=RetrievalMode.HYBRID,
        ),
        "retrieval_result": RetrievalResult(
            fragment_id="frag_12",
            source_id="src_licencias_v3",
            title="Renovación de licencia — versión demo 3",
            text="Presentar identificación oficial vigente y comprobante de pago.",
            lexical_score=0.72,
            vector_score=0.88,
            fused_score=0.91,
            citation=LICENSE_CITATION,
        ),
        "retrieval_response": RetrievalResponse(
            results=[
                RetrievalResult(
                    fragment_id="frag_12",
                    source_id="src_licencias_v3",
                    title="Renovación de licencia — versión demo 3",
                    text="Presentar identificación oficial vigente.",
                    fused_score=0.91,
                    citation=LICENSE_CITATION,
                )
            ],
            corpus_version=DEMO_CORPUS_VERSION,
            filtered_count=2,
        ),
        "ingestion_result": IngestionResult(
            corpus_version=DEMO_CORPUS_VERSION,
            domain=Domain.VEHICULOS,
            outcomes={IngestionOutcome.CREATED: 1, IngestionOutcome.UNCHANGED: 3},
            checksums={"doc_licencias_01": CHECKSUM},
            chunks_created=1,
        ),
        # §5.4
        "tool_metadata": RESERVE_TOOL,
        "tool_call": RESERVE_CALL,
        "tool_result": RESERVE_RESULT,
        "tool_error": ToolError(
            error=NormalizedError.from_code(
                ErrorCode.TOOL_TIMEOUT,
                "La tool no respondió dentro del deadline.",
                outcome=Outcome.UNKNOWN,
            ),
            provider="mock",
            safe_details={"timeout_ms": 5000},
        ),
        "integration_draft": IntegrationDraft(
            integration_id="intg_citas_demo",
            state=IntegrationState.DRAFT,
            title="Citas de demostración",
            domain=Domain.VEHICULOS,
            proposed_tools=[RESERVE_TOOL],
            # No es un secreto sino una referencia a uno: el valor se resuelve
            # fuera del repositorio (`DIE-F0-033`). El linter no distingue.
            auth_secret_ref="secret://demo/citas/token",  # noqa: S106
            egress_allowlist=["example.invalid"],
            created_at=FIXED_NOW,
        ),
        "mapper_validation": MapperValidation(
            integration_id="intg_citas_demo",
            passed=False,
            findings=["operación de escritura sin revisión humana"],
            blocked_reasons=["write_requires_human_review"],
            validated_at=FIXED_NOW,
        ),
        "controlled_test_result": ControlledTestResult(
            integration_id="intg_citas_demo",
            tool_name="vehiculos.reservar_cita",
            passed=True,
            used_synthetic_data=True,
            request_summary={"slot_id": "slot_101"},
            response_summary={"folio": "NEXO-MOCK-2026-000101"},
            tested_at=FIXED_NOW,
        ),
        "approval": Approval(
            integration_id="intg_citas_demo",
            approved_by="usr_admin_demo",
            approved_at=FIXED_NOW,
            diff_digest="sha256:demo",
            version="1.0.0",
            notes="Aprobado para demostración con datos sintéticos.",
        ),
        "published_tool_version": PublishedToolVersion(
            integration_id="intg_citas_demo",
            metadata=RESERVE_TOOL,
            state=IntegrationState.PUBLISHED,
            published_at=FIXED_NOW,
            approved_by="usr_admin_demo",
        ),
        # §5.5
        "catalog_descriptor": CatalogDescriptor(
            catalog_id=CITIZEN_CATALOG,
            version="1.0.0",
            title="Nexo IA Citizen Catalog v1",
            audience="citizen",
            components=[
                ComponentDescriptor(
                    name="Column",
                    schema_ref="a2ui://basic/Column",
                    allows_children=True,
                ),
                ComponentDescriptor(name="Text", schema_ref="a2ui://basic/Text"),
                ComponentDescriptor(
                    name="Button", schema_ref="a2ui://basic/Button", is_interactive=True
                ),
            ],
        ),
        "component_descriptor": ComponentDescriptor(
            name="Checklist",
            schema_ref="a2ui://nexo/Checklist",
            allows_children=True,
        ),
        "a2ui_message": SURFACE.messages[0],
        "a2ui_component": A2UIComponent(
            id="confirm",
            component="Button",
            properties={"label": "Confirmar cita"},
            action_id="act_reserve_01",
        ),
        "a2ui_surface": SURFACE,
        "a2ui_action": SURFACE.actions[0],
        "a2ui_validation_result": A2UIValidationResult(
            surface_id="surf_licencia",
            catalog_id=CITIZEN_CATALOG,
            outcome=A2UIValidationOutcome.VALID,
        ),
        "channel_fallback": ChannelFallback(
            channel=Channel.WHATSAPP,
            reason="component_not_supported",
            text="Renovación de licencia. Requisitos:",
            numbered_items=["1. Identificación oficial vigente"],
            action_hint="Responde CONFIRMAR para reservar tu cita.",
        ),
        # §5.6
        "model_task": ModelTask(
            task_kind=ModelTaskKind.VERIFICATION,
            requested_alias="high_accuracy",
            output_schema_ref="contracts://agent_result.v1",
            estimated_input_tokens=7800,
            risk=RiskLevel.HIGH,
            latency_budget_ms=8000,
            max_cost_usd=0.08,
        ),
        "model_policy": ModelPolicy(
            task_kind=ModelTaskKind.VERIFICATION,
            default_alias="high_accuracy",
            escalation_alias="reasoning",
            fallback_alias="general",
            min_accuracy_class=RiskLevel.HIGH,
            policy_version="policies-2026-07-30",
        ),
        "model_capabilities": ModelCapabilities(
            supports_structured_output=True,
            max_context_tokens=200_000,
            max_output_tokens=8192,
            cost_per_1k_input_usd=0.003,
            cost_per_1k_output_usd=0.015,
        ),
        "model_candidate": MODEL_DECISION.considered[0],
        "model_decision": MODEL_DECISION,
        "model_invocation": ModelInvocation(
            invocation_id="mdl_01",
            run_id="run_01JNE8ZP",
            trace_id="trace_01JNE8ZP",
            decision=MODEL_DECISION,
            attempt=1,
            input_tokens=7800,
            output_tokens=420,
            estimated_cost_usd=0.029,
            duration_ms=1830,
            schema_valid=True,
            started_at=FIXED_NOW,
        ),
        "self_check_result": SelfCheckResult(schema_valid=True, unsupported_claims=0),
        "deterministic_evaluation_result": DeterministicEvaluationResult(
            case_id="CAP-VEH-01",
            dataset_version="capstone_v1",
            domain_match=True,
            procedure_match=True,
            source_coverage=1.0,
            citation_precision=0.95,
            unsupported_critical_claims=0,
            tool_selection_correct=True,
            permission_compliance=True,
            a2ui_schema_valid=True,
            write_verifiable=True,
            questions_asked=1,
            max_questions_allowed=1,
        ),
        "judge_request": JudgeRequest(
            evaluation_id="eval_01",
            run_id="run_01JNE8ZP",
            rubric_version="capstone-v1",
            user_request="Quiero renovar mi licencia y saber si debo algo",
            answer="Puedes renovar tu licencia presentando identificación oficial vigente.",
            fact_ids=["fact_req_01", "fact_cost_01"],
            domain=Domain.VEHICULOS,
            generator_model="general",
            judge_model="judge_secondary",
        ),
        "judge_result": JudgeResult(
            evaluation_id="eval_01",
            run_id="run_01JNE8ZP",
            rubric_version="capstone-v1",
            generator_model="general",
            judge_model="judge_secondary",
            scores=JudgeScores(
                domain_accuracy=1.0,
                tool_selection=1.0,
                faithfulness=0.95,
                completeness=0.90,
                clarity=0.92,
                a2ui_quality=0.88,
                permission_compliance=1.0,
            ),
            passed=True,
            evaluated_at=FIXED_NOW,
        ),
        "evaluation_report": EvaluationReport(
            report_id="eval_report_01",
            dataset_version="capstone_v1",
            rubric_version="capstone-v1",
            corpus_versions={Domain.VEHICULOS: DEMO_CORPUS_VERSION},
            config_version="policies-2026-07-30",
            seed=1234,
            generated_at=FIXED_NOW,
        ),
        # §5.7
        "skill_manifest": SkillManifest(
            skill_id="skill_renovar_licencia",
            version="1.0.0",
            title="Renovar licencia de conducir",
            domain=Domain.VEHICULOS,
            objective="Reunir requisitos, adeudo y cita para renovar una licencia.",
            owner="equipo-nexo",
            steps=[
                SkillStep(
                    step_id="recuperar_requisitos",
                    agent=AgentName.DOMAIN_NAVIGATOR,
                    objective="Recuperar requisitos vigentes con citas.",
                ),
                SkillStep(
                    step_id="verificar",
                    agent=AgentName.VERIFIER,
                    objective="Verificar requisitos y costos.",
                    depends_on=["recuperar_requisitos"],
                    parallel_group="consolidacion",
                ),
                SkillStep(
                    step_id="estimar",
                    agent=AgentName.ESTIMATOR,
                    objective="Calcular costo total y documentos faltantes.",
                    depends_on=["recuperar_requisitos"],
                    parallel_group="consolidacion",
                ),
            ],
            allowed_sources=["src_licencias_v3"],
            allowed_tools=["vehiculos.consultar_adeudo", "vehiculos.reservar_cita"],
            confirmation_required_for=["vehiculos.reservar_cita"],
            budgets=SkillBudgets(deadline_ms=20000, max_questions=1),
            success_criteria=["Cita reservada con folio verificable"],
            escalation_policy="Si no hay evidencia suficiente, responder parcial con warning.",
        ),
        # §5.8
        "run_event": RUN_EVENT,
        "event_sequence": EventSequence(
            run_id="run_01JNE8ZP",
            events=[
                RunEvent(
                    event_id="evt_01",
                    trace_id="trace_01JNE8ZP",
                    run_id="run_01JNE8ZP",
                    sequence=1,
                    type=EventType.RUN_QUEUED,
                    timestamp=FIXED_NOW,
                    actor=EventActor(type=ActorType.SYSTEM, name="supervisor"),
                    status=EventStatus.SUCCEEDED,
                    correlation_id="trace_01JNE8ZP",
                ),
                RunEvent(
                    event_id="evt_02",
                    trace_id="trace_01JNE8ZP",
                    run_id="run_01JNE8ZP",
                    sequence=2,
                    type=EventType.RUN_STARTED,
                    timestamp=FIXED_NOW,
                    actor=EventActor(type=ActorType.SYSTEM, name="supervisor"),
                    status=EventStatus.SUCCEEDED,
                    correlation_id="trace_01JNE8ZP",
                    parent_event_id="evt_01",
                ),
            ],
        ),
        # Compartidos
        "normalized_error": NormalizedError.from_code(
            ErrorCode.PERMISSION_DENIED,
            "El rol no autoriza esta operación en el dominio solicitado.",
        ),
    }


VALID_EXAMPLES: dict[str, NexoModel] = _valid_examples()


class InvalidExample(NamedTuple):
    """Payload que un contrato debe rechazar, con la regla que lo detecta."""

    name: str
    contract: str
    rule: str
    payload: dict[str, Any]


def _base(contract: str) -> dict[str, Any]:
    """Serialización del ejemplo válido, punto de partida de cada caso inválido."""
    return VALID_EXAMPLES[contract].model_dump(mode="json", by_alias=True)


def _mutate(contract: str, **changes: Any) -> dict[str, Any]:
    payload = _base(contract)
    payload.update(changes)
    return payload


def _invalid_examples() -> list[InvalidExample]:
    """Casos inválidos que cubren cada invariante escrito en los contratos."""
    unconfirmed_action = _mutate("action_request", status="confirmed", consent=False)

    non_write_agent_result = _base("agent_result")
    non_write_agent_result["agent"] = "domain_navigator"
    non_write_agent_result["proposed_tools"] = [
        {
            "name": "vehiculos.reservar_cita",
            "mode": "write",
            "rationale": "quiere reservar",
            "parameters": {},
        }
    ]

    uncited_critical = _mutate("verified_fact", citations=[])

    expired_citation = _base("verified_fact")
    expired_citation["citations"][0]["is_active"] = False

    write_without_confirmation = _mutate("tool_metadata", requires_confirmation=False)
    write_call_without_key = _mutate("tool_call", idempotency_key=None)

    retryable_unknown = _mutate("normalized_error", retryable=True, outcome="unknown")

    non_monotonic = _base("event_sequence")
    non_monotonic["events"][1]["sequence"] = 5

    unknown_action_component = _base("a2ui_surface")
    unknown_action_component["actions"] = []

    surface_without_create = _base("a2ui_surface")
    surface_without_create["messages"] = surface_without_create["messages"][1:]

    rootless_components = {
        "surfaceId": "surf_licencia",
        "components": [{"id": "title", "component": "Text", "text": "hola"}],
    }

    secret_in_event = _mutate("run_event", data={"api_key": "sk-demo"})
    pii_in_event = _mutate("run_event", data={"telefono": "6181234567"})

    naive_timestamp = _mutate("run_event", timestamp="2026-07-30T15:00:00")

    bad_id_prefix = _mutate("run_request", run_id="job_01JNE8ZP")
    pii_shaped_id = _mutate("run_request", conversation_id="conv_6181234567")

    unpriced_total = _base("estimate")
    unpriced_total["total_cost"]["amount_minor"] = 999999

    cyclic_estimate = _base("estimate")
    cyclic_estimate["steps"][0]["depends_on"] = ["licencia_funcionamiento"]

    judge_same_model = _mutate("judge_request", judge_model="general")

    waiting_without_action = _mutate("run_state", pending_action=None)

    succeeded_without_folio = _base("action_result")
    succeeded_without_folio["tool_result"]["confirmation"] = None

    unknown_property = _mutate("run_request", unexpected_field="valor")

    score_out_of_range = _mutate("retrieval_result", fused_score=1.4)

    rejected_dependency = _base("verified_facts")
    rejected_dependency["facts"][0]["verification"] = "rejected"
    rejected_dependency["facts"][0]["write_eligible"] = False
    rejected_dependency["facts"][1]["depends_on"] = ["fact_req_01"]

    skill_widens_permissions = _base("skill_manifest")
    skill_widens_permissions["confirmation_required_for"] = ["ganaderia.registrar_vacuna"]

    wrong_tool_prefix = _mutate("tool_metadata", name="autos.reservar_cita")

    return [
        InvalidExample(
            "action_request__confirmed_without_consent",
            "action_request",
            "una acción confirmada exige consentimiento explícito",
            unconfirmed_action,
        ),
        InvalidExample(
            "agent_result__non_transactional_proposes_write",
            "agent_result",
            "solo el agente transaccional puede proponer tools de escritura",
            non_write_agent_result,
        ),
        InvalidExample(
            "verified_fact__critical_accepted_without_citation",
            "verified_fact",
            "un hecho crítico aceptado exige citación activa",
            uncited_critical,
        ),
        InvalidExample(
            "verified_fact__critical_accepted_with_expired_citation",
            "verified_fact",
            "una citación inactiva no sostiene un hecho crítico",
            expired_citation,
        ),
        InvalidExample(
            "tool_metadata__write_without_confirmation",
            "tool_metadata",
            "una tool de escritura debe exigir confirmación",
            write_without_confirmation,
        ),
        InvalidExample(
            "tool_metadata__prefix_does_not_match_domain",
            "tool_metadata",
            "el prefijo de la tool debe corresponder a su dominio",
            wrong_tool_prefix,
        ),
        InvalidExample(
            "tool_call__write_without_idempotency_key",
            "tool_call",
            "una escritura exige idempotency_key",
            write_call_without_key,
        ),
        InvalidExample(
            "normalized_error__retryable_with_unknown_outcome",
            "normalized_error",
            "un outcome desconocido nunca es reintentable",
            retryable_unknown,
        ),
        InvalidExample(
            "event_sequence__non_monotonic",
            "event_sequence",
            "la secuencia por run es estrictamente monotónica",
            non_monotonic,
        ),
        InvalidExample(
            "run_event__secret_in_payload",
            "run_event",
            "los eventos no transportan secretos",
            secret_in_event,
        ),
        InvalidExample(
            "run_event__pii_in_payload",
            "run_event",
            "los eventos no transportan PII directa",
            pii_in_event,
        ),
        InvalidExample(
            "run_event__naive_timestamp",
            "run_event",
            "los timestamps exigen zona horaria",
            naive_timestamp,
        ),
        InvalidExample(
            "run_request__unregistered_id_prefix",
            "run_request",
            "los IDs usan prefijos registrados",
            bad_id_prefix,
        ),
        InvalidExample(
            "run_request__id_looks_like_pii",
            "run_request",
            "un ID opaco no incrusta secuencias que parezcan teléfonos",
            pii_shaped_id,
        ),
        InvalidExample(
            "run_request__unknown_property",
            "run_request",
            "los contratos rechazan propiedades desconocidas",
            unknown_property,
        ),
        InvalidExample(
            "a2ui_surface__action_not_declared",
            "a2ui_surface",
            "un componente no dispara una acción no declarada",
            unknown_action_component,
        ),
        InvalidExample(
            "a2ui_surface__missing_create_surface",
            "a2ui_surface",
            "la superficie debe abrir con createSurface",
            surface_without_create,
        ),
        InvalidExample(
            "a2ui_component_tree__without_root",
            "a2ui_message",
            "el árbol exige exactamente un componente root",
            {"version": "v0.9.1", "updateComponents": rootless_components},
        ),
        InvalidExample(
            "estimate__total_does_not_match_steps",
            "estimate",
            "el total se suma en código y debe cuadrar",
            unpriced_total,
        ),
        InvalidExample(
            "estimate__cyclic_dependencies",
            "estimate",
            "el DAG de permisos no admite ciclos",
            cyclic_estimate,
        ),
        InvalidExample(
            "judge_request__same_model_as_generator",
            "judge_request",
            "el judge usa un modelo distinto al generador",
            judge_same_model,
        ),
        InvalidExample(
            "run_state__waiting_confirmation_without_action",
            "run_state",
            "esperar confirmación exige una acción persistida",
            waiting_without_action,
        ),
        InvalidExample(
            "action_result__succeeded_without_verifiable_folio",
            "action_result",
            "sin identificador verificable no hay éxito",
            succeeded_without_folio,
        ),
        InvalidExample(
            "retrieval_result__score_out_of_range",
            "retrieval_result",
            "los puntajes están acotados a [0, 1]",
            score_out_of_range,
        ),
        InvalidExample(
            "verified_facts__accepted_fact_depends_on_rejected",
            "verified_facts",
            "un hecho aceptado no puede depender de uno rechazado",
            rejected_dependency,
        ),
        InvalidExample(
            "skill_manifest__confirmation_outside_allowlist",
            "skill_manifest",
            "una skill no amplía permisos",
            skill_widens_permissions,
        ),
    ]


INVALID_EXAMPLES: list[InvalidExample] = _invalid_examples()
