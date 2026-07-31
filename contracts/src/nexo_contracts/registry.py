"""Registro explícito de los contratos publicados.

Se declara a mano en lugar de descubrirse por introspección: publicar un
contrato es una decisión, no un efecto secundario de haber creado una clase.
El exportador de JSON Schema y los contract tests recorren este registro, así
que un contrato ausente de aquí simplemente no se publica.

La clave es el nombre publicado (`snake_case`), que se convierte en el nombre
del archivo `contracts/jsonschema/<clave>.v1.json` y en la referencia
`contracts://<clave>.v1` usada por tools y actions.
"""

from __future__ import annotations

from .a2ui import (
    A2UIAction,
    A2UIComponent,
    A2UIMessage,
    A2UISurface,
    A2UIValidationResult,
    CatalogDescriptor,
    ChannelFallback,
    ComponentDescriptor,
)
from .base import NexoModel
from .errors import NormalizedError
from .estimation import Estimate
from .evaluation import (
    DeterministicEvaluationResult,
    EvaluationReport,
    JudgeRequest,
    JudgeResult,
    SelfCheckResult,
)
from .events import EventSequence, RunEvent
from .execution import (
    ActionRequest,
    ActionResult,
    AgentResult,
    AgentTask,
    RunRequest,
    RunResult,
    RunSnapshot,
    RunState,
)
from .facts import (
    CandidateFact,
    Contradiction,
    Deduction,
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
from .rag import (
    Chunk,
    CorpusVersion,
    Document,
    DocumentVersion,
    IngestionResult,
    RetrievalQuery,
    RetrievalResponse,
    RetrievalResult,
    Source,
)
from .skills import SkillManifest
from .tools import (
    Approval,
    ControlledTestResult,
    IntegrationDraft,
    MapperValidation,
    PublishedToolVersion,
    ToolCall,
    ToolError,
    ToolMetadata,
    ToolResult,
)

# §5.1 — contratos de ejecución
EXECUTION_CONTRACTS: dict[str, type[NexoModel]] = {
    "run_request": RunRequest,
    "run_state": RunState,
    "run_result": RunResult,
    "run_snapshot": RunSnapshot,
    "agent_task": AgentTask,
    "agent_result": AgentResult,
    "action_request": ActionRequest,
    "action_result": ActionResult,
}

# §5.2 — hechos y evidencia
FACT_CONTRACTS: dict[str, type[NexoModel]] = {
    "candidate_fact": CandidateFact,
    "verified_fact": VerifiedFact,
    "verified_facts": VerifiedFacts,
    "source_citation": SourceCitation,
    "contradiction": Contradiction,
    "deduction": Deduction,
    "estimate": Estimate,
}

# §5.3 — RAG
RAG_CONTRACTS: dict[str, type[NexoModel]] = {
    "source": Source,
    "document": Document,
    "document_version": DocumentVersion,
    "chunk": Chunk,
    "corpus_version": CorpusVersion,
    "retrieval_query": RetrievalQuery,
    "retrieval_result": RetrievalResult,
    "retrieval_response": RetrievalResponse,
    "ingestion_result": IngestionResult,
}

# §5.4 — MCP
TOOL_CONTRACTS: dict[str, type[NexoModel]] = {
    "tool_metadata": ToolMetadata,
    "tool_call": ToolCall,
    "tool_result": ToolResult,
    "tool_error": ToolError,
    "integration_draft": IntegrationDraft,
    "mapper_validation": MapperValidation,
    "controlled_test_result": ControlledTestResult,
    "approval": Approval,
    "published_tool_version": PublishedToolVersion,
}

# §5.5 — A2UI
A2UI_CONTRACTS: dict[str, type[NexoModel]] = {
    "catalog_descriptor": CatalogDescriptor,
    "component_descriptor": ComponentDescriptor,
    "a2ui_message": A2UIMessage,
    "a2ui_component": A2UIComponent,
    "a2ui_surface": A2UISurface,
    "a2ui_action": A2UIAction,
    "a2ui_validation_result": A2UIValidationResult,
    "channel_fallback": ChannelFallback,
}

# §5.6 — modelos y evaluación
MODEL_CONTRACTS: dict[str, type[NexoModel]] = {
    "model_task": ModelTask,
    "model_policy": ModelPolicy,
    "model_capabilities": ModelCapabilities,
    "model_candidate": ModelCandidate,
    "model_decision": ModelDecision,
    "model_invocation": ModelInvocation,
    "self_check_result": SelfCheckResult,
    "deterministic_evaluation_result": DeterministicEvaluationResult,
    "judge_request": JudgeRequest,
    "judge_result": JudgeResult,
    "evaluation_report": EvaluationReport,
}

# §5.7 — skills operativas
SKILL_CONTRACTS: dict[str, type[NexoModel]] = {
    "skill_manifest": SkillManifest,
}

# §5.8 — eventos
EVENT_CONTRACTS: dict[str, type[NexoModel]] = {
    "run_event": RunEvent,
    "event_sequence": EventSequence,
}

SHARED_CONTRACTS: dict[str, type[NexoModel]] = {
    "normalized_error": NormalizedError,
}

CONTRACT_REGISTRY: dict[str, type[NexoModel]] = {
    **EXECUTION_CONTRACTS,
    **FACT_CONTRACTS,
    **RAG_CONTRACTS,
    **TOOL_CONTRACTS,
    **A2UI_CONTRACTS,
    **MODEL_CONTRACTS,
    **SKILL_CONTRACTS,
    **EVENT_CONTRACTS,
    **SHARED_CONTRACTS,
}
"""Todos los contratos publicados de §5, por nombre estable."""


def contract_for(name: str) -> type[NexoModel]:
    try:
        return CONTRACT_REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"contrato no registrado: {name!r}. Los contratos publicados son "
            f"{sorted(CONTRACT_REGISTRY)}"
        ) from None
