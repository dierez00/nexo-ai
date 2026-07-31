"""Enumeraciones cerradas y versionadas (`DIE-F0-012`).

Ningún estado, dominio, modo, riesgo, error o tipo de evento se representa con
texto libre. Añadir un miembro es un cambio aditivo compatible; renombrar o
eliminar uno obliga a publicar una versión nueva de contratos (`DIE-F0-007`).
"""

from __future__ import annotations

from enum import StrEnum


class Domain(StrEnum):
    """Los cinco namespaces iniciales (§2.3). Un dominio fuera de esta lista se rechaza."""

    VEHICULOS = "vehiculos"
    AYUNTAMIENTO_EMPRESAS = "ayuntamiento_empresas"
    REGISTRO_CIVIL = "registro_civil"
    SALUD = "salud"
    GANADERIA = "ganaderia"


class Channel(StrEnum):
    WEB = "web"
    WHATSAPP = "whatsapp"
    VOICE = "voice"


class Audience(StrEnum):
    """Perfiles de destinatario. La personalización nunca altera hechos (`DIE-F4-079`)."""

    CITIZEN = "citizen"
    SENIOR = "senior"
    PRODUCER = "producer"
    BUSINESS = "business"
    PUBLIC_SERVANT = "public_servant"
    TECHNICAL = "technical"
    LOW_DIGITAL_LITERACY = "low_digital_literacy"


class OperationalUrgency(StrEnum):
    """Urgencia **operativa** de una solicitud, no clínica ni jurídica.

    Describe cuánto aprieta el plazo del trámite, y nada más. En salud (Fase 2)
    la distinción es crítica: `URGENT` significa «la cita vence mañana», nunca
    «esta persona necesita atención inmediata». Clasificar urgencia clínica
    sería diagnosticar, que está prohibido (§2.3).
    """

    ROUTINE = "routine"
    TIME_SENSITIVE = "time_sensitive"
    URGENT = "urgent"


class RunStatus(StrEnum):
    """Estados de un run (arquitectura §9.11).

    `queued → planning → running → waiting_confirmation → running →
    succeeded | partial | failed`; `cancelled` puede ocurrir antes del final.
    """

    QUEUED = "queued"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING_CONFIRMATION = "waiting_confirmation"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_RUN_STATUSES: frozenset[RunStatus] = frozenset(
    {RunStatus.SUCCEEDED, RunStatus.PARTIAL, RunStatus.FAILED, RunStatus.CANCELLED}
)


class AgentName(StrEnum):
    """Agentes de la matriz §13. El catálogo cerrado impide delegar a un agente inexistente."""

    CLASSIFIER = "classifier"
    SUPERVISOR = "supervisor"
    DOMAIN_NAVIGATOR = "domain_navigator"
    VERIFIER = "verifier"
    ESTIMATOR = "estimator"
    TRANSACTIONAL = "transactional"
    WRITER = "writer"
    SIGNAL_ANALYST = "signal_analyst"
    JUDGE = "judge"
    PROMPT_ASSISTANT = "prompt_assistant"


class TaskStatus(StrEnum):
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


class VerificationStatus(StrEnum):
    """Resultado de verificar un hecho candidato (`DIE-F1-052`)."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNCERTAIN = "uncertain"


class FactCategory(StrEnum):
    """Naturaleza de un hecho. Determina si su citación es obligatoria."""

    REQUIREMENT = "requirement"
    COST = "cost"
    LOCATION = "location"
    VALIDITY = "validity"
    SCHEDULE = "schedule"
    DEPENDENCY = "dependency"
    PROCEDURE = "procedure"
    ACTION_RESULT = "action_result"
    CONTEXT = "context"


CRITICAL_FACT_CATEGORIES: frozenset[FactCategory] = frozenset(
    {
        FactCategory.REQUIREMENT,
        FactCategory.COST,
        FactCategory.LOCATION,
        FactCategory.VALIDITY,
        FactCategory.DEPENDENCY,
        FactCategory.ACTION_RESULT,
    }
)
"""Categorías cuyos claims exigen citación activa al 100% (§3, gate de grounding).

`SCHEDULE`, `PROCEDURE` y `CONTEXT` quedan fuera porque describen orientación y
contexto deducido, no compromisos verificables sobre requisitos, dinero,
ubicación, vigencia, dependencias ni resultados de una escritura.
"""


class FactOrigin(StrEnum):
    """De dónde salió un hecho candidato. Sirve para detectar contradicciones tool ↔ documento."""

    RAG = "rag"
    TOOL = "tool"
    USER = "user"
    PROFILE = "profile"
    DEDUCTION = "deduction"
    CATALOG = "catalog"


class ContradictionSeverity(StrEnum):
    """Una contradicción crítica bloquea toda escritura dependiente (`DIE-F4-020`)."""

    INFORMATIONAL = "informational"
    MATERIAL = "material"
    CRITICAL = "critical"


class ContradictionStatus(StrEnum):
    DETECTED = "detected"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


class ToolMode(StrEnum):
    """Modo de una tool. Solo `WRITE` puede producir efectos externos."""

    READ = "read"
    WRITE = "write"
    COMPUTE = "compute"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ToolCallStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DENIED = "denied"
    TIMEOUT = "timeout"


class Outcome(StrEnum):
    """Certeza sobre el efecto de una operación.

    `UNKNOWN` es el caso peligroso: un write con outcome desconocido nunca se
    reintenta automáticamente y produce `partial` (`DIE-F1-077`, `DIE-F1-081`).
    """

    KNOWN_SUCCESS = "known_success"
    KNOWN_FAILURE = "known_failure"
    UNKNOWN = "unknown"


class ActionStatus(StrEnum):
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class ErrorCode(StrEnum):
    """Códigos de error estables (arquitectura §9.11).

    El consumidor decide por `code`, nunca por el texto del mensaje.
    """

    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    APPOINTMENT_CONFLICT = "APPOINTMENT_CONFLICT"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    ACTION_CONFIRMATION_REQUIRED = "ACTION_CONFIRMATION_REQUIRED"
    RATE_LIMITED = "RATE_LIMITED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    MODEL_OUTPUT_INVALID = "MODEL_OUTPUT_INVALID"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    RUN_TIMEOUT = "RUN_TIMEOUT"
    RUN_CANCELLED = "RUN_CANCELLED"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"
    CONFIGURATION_INVALID = "CONFIGURATION_INVALID"
    CONTRACT_INVALID = "CONTRACT_INVALID"


RETRYABLE_ERROR_CODES: frozenset[ErrorCode] = frozenset(
    {
        ErrorCode.RATE_LIMITED,
        ErrorCode.PROVIDER_ERROR,
        ErrorCode.MODEL_UNAVAILABLE,
        ErrorCode.TOOL_TIMEOUT,
    }
)
"""Errores reintentables *solo* para operaciones de lectura o idempotentes.

`UNKNOWN_OUTCOME` queda deliberadamente fuera: es la condición que prohíbe el
reintento automático de una escritura (`DIE-F0-035`).
"""


class SourceStatus(StrEnum):
    """Estado de una fuente documental. Solo `ACTIVE` alimenta el retrieval."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"


class CorpusStatus(StrEnum):
    DRAFT = "draft"
    STAGED = "staged"
    ACTIVE = "active"
    ROLLED_BACK = "rolled_back"


class RetrievalMode(StrEnum):
    LEXICAL = "lexical"
    VECTOR = "vector"
    HYBRID = "hybrid"


class IngestionOutcome(StrEnum):
    CREATED = "created"
    UNCHANGED = "unchanged"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class ModelHealth(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class ModelTaskKind(StrEnum):
    """Tipo de tarea que consume el router para elegir política (`DIE-F3-001`)."""

    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    NAVIGATION = "navigation"
    SUPERVISION = "supervision"
    VERIFICATION = "verification"
    DRAFTING = "drafting"
    VISION = "vision"
    JUDGE = "judge"


class ModelDecisionReason(StrEnum):
    """Motivo de la decisión del router; se registra en eventos sin revelar secretos."""

    POLICY_DEFAULT = "policy_default"
    PRIMARY_PROVIDER_DEGRADED = "primary_provider_degraded"
    PRIMARY_PROVIDER_DOWN = "primary_provider_down"
    INVALID_OUTPUT_ESCALATION = "invalid_output_escalation"
    CONTEXT_LENGTH_EXCEEDED = "context_length_exceeded"
    BUDGET_EXHAUSTED = "budget_exhausted"
    DEADLINE_EXCEEDED = "deadline_exceeded"
    OFFLINE_PROFILE = "offline_profile"


class IntegrationState(StrEnum):
    """Ciclo de vida del MCP Mapper (`DIE-F3-011`).

    Se congela en Fase 0 aunque el Mapper sea trabajo de Fase 3: los estados
    forman parte de los contratos de §5.4 y no deben renegociarse después.
    """

    DRAFT = "draft"
    PARSED = "parsed"
    VALIDATED = "validated"
    TESTED = "tested"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


class A2UIMessageKind(StrEnum):
    """Los tres mensajes de A2UI v0.9.1 admitidos por el builder."""

    CREATE_SURFACE = "createSurface"
    UPDATE_DATA_MODEL = "updateDataModel"
    UPDATE_COMPONENTS = "updateComponents"


class A2UIValidationOutcome(StrEnum):
    VALID = "valid"
    INVALID = "invalid"


class EventType(StrEnum):
    """Familias mínimas de eventos (§5.8).

    El nombre es `dominio.acción` y es estable: el workflow viewer, el replay y
    las evaluaciones dependen de él.
    """

    RUN_QUEUED = "run.queued"
    RUN_PLANNING = "run.planning"
    RUN_STARTED = "run.started"
    RUN_WAITING_CONFIRMATION = "run.waiting_confirmation"
    RUN_RESUMED = "run.resumed"
    RUN_PARTIAL = "run.partial"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"
    RUN_CANCELLED = "run.cancelled"

    CLASSIFICATION_STARTED = "classification.started"
    CLASSIFICATION_COMPLETED = "classification.completed"
    CLASSIFICATION_FAILED = "classification.failed"

    PLAN_CREATED = "plan.created"
    PLAN_UPDATED = "plan.updated"

    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_RETRIED = "agent.retried"
    AGENT_FAILED = "agent.failed"

    RAG_STARTED = "rag.started"
    RAG_COMPLETED = "rag.completed"
    RAG_FILTERED = "rag.filtered"
    RAG_FAILED = "rag.failed"

    TOOL_REQUESTED = "tool.requested"
    TOOL_AUTHORIZED = "tool.authorized"
    TOOL_DENIED = "tool.denied"
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    TOOL_REPLAYED = "tool.replayed"
    TOOL_FAILED = "tool.failed"

    MODEL_SELECTED = "model.selected"
    MODEL_FALLBACK = "model.fallback"
    MODEL_COMPLETED = "model.completed"
    MODEL_FAILED = "model.failed"

    VERIFICATION_COMPLETED = "verification.completed"
    CONTRADICTION_DETECTED = "contradiction.detected"
    CONTRADICTION_RESOLVED = "contradiction.resolved"
    CONTRADICTION_UNRESOLVED = "contradiction.unresolved"

    CHECKPOINT_SAVED = "checkpoint.saved"
    CHECKPOINT_RESTORED = "checkpoint.restored"

    A2UI_GENERATED = "a2ui.generated"
    A2UI_VALIDATED = "a2ui.validated"
    A2UI_VALIDATION_FAILED = "a2ui.validation_failed"
    A2UI_FALLBACK = "a2ui.fallback"

    EVALUATION_STARTED = "evaluation.started"
    EVALUATION_COMPLETED = "evaluation.completed"
    EVALUATION_FAILED = "evaluation.failed"

    PROMPT_DRAFTED = "prompt.drafted"
    PROMPT_VALIDATED = "prompt.validated"
    PROMPT_APPROVED = "prompt.approved"
    PROMPT_REJECTED = "prompt.rejected"
    PROMPT_PUBLISHED = "prompt.published"

    CORPUS_DRAFTED = "corpus.drafted"
    CORPUS_VALIDATED = "corpus.validated"
    CORPUS_ACTIVATED = "corpus.activated"
    CORPUS_ROLLED_BACK = "corpus.rolled_back"


class ActorType(StrEnum):
    """Quién origina un evento."""

    SUPERVISOR = "supervisor"
    AGENT = "agent"
    TOOL = "tool"
    MODEL = "model"
    RETRIEVER = "retriever"
    SYSTEM = "system"
    USER = "user"


class EventStatus(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DENIED = "denied"
    SKIPPED = "skipped"


class EventVisibility(StrEnum):
    """Quién puede consumir el payload detallado de un evento."""

    PUBLIC = "public"
    RESTRICTED = "restricted"
