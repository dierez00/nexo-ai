"""A2UI ciudadano mínimo: catálogo, builder, validator y fallback (F1.13 parcial).

Cubre los cuatro casos adversariales que exige §8.18: superficie válida,
componente no permitido, binding roto y acción falsificada.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from nexo_a2ui import (
    CITIZEN_CATALOG,
    CITIZEN_CATALOG_ID,
    CITIZEN_FREEZE_PATH,
    CitizenSurfaceBuilder,
    SurfaceValidator,
    build_fallback,
    export_catalog,
    format_money,
    load_catalog,
    load_jsonl,
    render_catalog_json,
    render_jsonl,
    surface_from_messages,
    verify_frozen_catalog,
)
from nexo_agents.domain_manifest import load_domain
from nexo_contracts import (
    A2UI_PROTOCOL_VERSION,
    A2UIAction,
    A2UIComponent,
    A2UIMessage,
    A2UIMessageKind,
    ActionRequest,
    Channel,
    ConfigurationError,
    Domain,
    Estimate,
    EstimateStep,
    FactCategory,
    FactValue,
    Money,
    SourceCitation,
    UpdateComponents,
    VerificationStatus,
    VerifiedFact,
    VerifiedFacts,
)
from nexo_rag.corpus.cli import repository_root

pytestmark = pytest.mark.unit

NOW = datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)
SURFACE_ID = "surf_licencia"

CITATION = SourceCitation(
    source_id="src_veh_licencias",
    fragment_id="frag_nwndatdrgfnfnnih",
    corpus_version="vehiculos-2026-07-30",
    source_version="v3",
    valid_from=NOW.date(),
    is_active=True,
)


def _fact(fact_id: str, claim: str, category: FactCategory, **value: object) -> VerifiedFact:
    return VerifiedFact(
        fact_id=fact_id,
        claim=claim,
        value=FactValue(**value),  # type: ignore[arg-type]
        category=category,
        domain="vehiculos",  # type: ignore[arg-type]
        verification=VerificationStatus.ACCEPTED,
        reason="citation_supports_claim",
        confidence=0.95,
        citations=[CITATION],
    )


@pytest.fixture
def facts() -> VerifiedFacts:
    return VerifiedFacts(
        snapshot_id="snapshot_cap_veh_01",
        created_at=NOW,
        facts=(
            _fact(
                "fact_req_01",
                "Identificación oficial vigente.",
                FactCategory.REQUIREMENT,
                items=["Identificación oficial vigente"],
            ),
            _fact(
                "fact_cost_01",
                "Renovación a tres años.",
                FactCategory.COST,
                money=Money(amount_minor=81400, currency="MXN"),
            ),
            _fact(
                "fact_proc_01",
                "El trámite es presencial y requiere cita.",
                FactCategory.PROCEDURE,
                text="presencial",
            ),
        ),
    )


@pytest.fixture
def action() -> ActionRequest:
    return ActionRequest(
        action_id="act_reserve_01",
        run_id="run_000001",
        tool_name="vehiculos.reservar_cita",
        input_schema_ref="contracts://tools/vehiculos.reservar_cita.input.v1",
        tool_version="1.0.0",
        expected_version=1,
        parameters={"slot_id": "slot_101"},
        required_permission="appointment:create",
    )


@pytest.fixture
def validator() -> SurfaceValidator:
    return SurfaceValidator(catalog=CITIZEN_CATALOG)


@pytest.fixture
def builder() -> CitizenSurfaceBuilder:
    return CitizenSurfaceBuilder()


# --- Catálogo (`DIE-F1-100`, `DIE-F1-101`) ----------------------------------


def test_the_published_catalog_matches_the_code() -> None:
    """El JSON es artefacto derivado; escribirlo a mano crearía dos verdades."""
    path = repository_root() / "a2ui/catalogs/citizen/v1/catalog.json"

    assert path.read_text(encoding="utf-8") == render_catalog_json()


def test_config_points_at_the_published_catalog() -> None:
    """`config/catalogs.yaml` declaraba una ruta que no existía (H1-08)."""
    from nexo_orchestration.configuration import load_config

    entry = next(
        item for item in load_config().catalogs.catalogs if item.catalog_id == CITIZEN_CATALOG_ID
    )
    assert (repository_root() / entry.path).exists()


def test_the_catalog_round_trips_through_its_contract() -> None:
    loaded = load_catalog(repository_root())

    assert loaded.catalog_id == CITIZEN_CATALOG_ID
    assert loaded.component_names() == CITIZEN_CATALOG.component_names()


def test_citizen_v1_freeze_matches_every_delivered_artifact() -> None:
    manifest = verify_frozen_catalog(repository_root())

    assert manifest.status == "frozen"
    assert manifest.protocol_version == A2UI_PROTOCOL_VERSION
    assert manifest.catalog_id == CITIZEN_CATALOG_ID


def test_export_refuses_to_change_the_frozen_catalog(tmp_path) -> None:
    source = repository_root() / CITIZEN_FREEZE_PATH
    target = tmp_path / CITIZEN_FREEZE_PATH
    target.parent.mkdir(parents=True)
    target.write_bytes(source.read_bytes())
    changed = CITIZEN_CATALOG.model_copy(update={"title": "Cambio incompatible"})

    with pytest.raises(ConfigurationError, match="publique un catalog_id v2"):
        export_catalog(tmp_path, changed)

    assert not (tmp_path / "a2ui/catalogs/citizen/v1/catalog.json").exists()


def test_only_two_components_are_interactive() -> None:
    """Cada componente interactivo es superficie de ataque que hay que validar."""
    interactive = {c.name for c in CITIZEN_CATALOG.components if c.is_interactive}

    assert interactive == {"SlotPicker", "ConfirmButton"}


@pytest.mark.parametrize("domain", [Domain.VEHICULOS, Domain.AYUNTAMIENTO_EMPRESAS])
def test_domain_component_references_exist_in_the_citizen_catalog(domain: Domain) -> None:
    manifest = load_domain(repository_root(), domain)

    assert set(manifest.a2ui_components) <= CITIZEN_CATALOG.component_names()


def test_schedule_facts_render_as_slot_picker(builder, validator, facts) -> None:
    schedule = facts.facts[0].model_copy(
        update={
            "fact_id": "fact_schedule",
            "claim": "Hay horarios disponibles.",
            "category": FactCategory.SCHEDULE,
            "value": FactValue(items=["2026-08-03T09:00:00Z · slot_01"]),
            "supporting_tool_call_id": "tc_000001",
            "citations": [],
        }
    )
    with_schedule = facts.model_copy(update={"facts": (*facts.facts, schedule)})

    surface = builder.build(with_schedule, surface_id=SURFACE_ID)
    result = validator.validate(surface)
    tree = next(
        message.update_components for message in surface.messages if message.update_components
    )

    assert result.is_valid
    assert "SlotPicker" in {component.component for component in tree.components}


# --- Builder (`DIE-F1-102`, `DIE-F1-103`) -----------------------------------


def test_a_built_surface_validates(builder, validator, facts, action) -> None:
    surface = builder.build(facts, surface_id=SURFACE_ID, pending_action=action)

    result = validator.validate(surface, run_action_ids=frozenset({action.action_id}))

    assert result.is_valid, result.errors


def test_the_surface_opens_with_create_and_carries_its_data(builder, facts) -> None:
    surface = builder.build(facts, surface_id=SURFACE_ID)

    kinds = [message.kind for message in surface.messages]
    assert kinds[0] is A2UIMessageKind.CREATE_SURFACE
    assert A2UIMessageKind.UPDATE_DATA_MODEL in kinds
    assert A2UIMessageKind.UPDATE_COMPONENTS in kinds


def test_the_builder_serializes_one_protocol_message_per_jsonl_line(builder, facts) -> None:
    surface = builder.build(facts, surface_id=SURFACE_ID)
    payload = render_jsonl(surface)

    assert len(payload.splitlines()) == len(surface.messages)
    assert all('"version":"v0.9.1"' in line for line in payload.splitlines())


def test_data_lives_in_the_data_model_not_in_the_tree(builder, facts) -> None:
    """`DIE-F1-102`: la estructura referencia por binding, no incrusta valores."""
    surface = builder.build(facts, surface_id=SURFACE_ID)
    tree = next(m for m in surface.messages if m.update_components is not None)

    serialized = tree.model_dump_json()
    assert "Identificación oficial vigente" not in serialized
    assert '"path"' in serialized


def test_only_accepted_facts_reach_the_surface(builder, validator) -> None:
    """Un hecho rechazado no se muestra: no es evidencia de nada."""
    rejected = VerifiedFacts(
        snapshot_id="snapshot_rechazado",
        created_at=NOW,
        facts=(
            VerifiedFact(
                fact_id="fact_bad_01",
                claim="La renovación es gratuita.",
                value=FactValue(text="gratis"),
                category=FactCategory.COST,
                domain="vehiculos",  # type: ignore[arg-type]
                verification=VerificationStatus.REJECTED,
                reason="source_expired",
                confidence=0.2,
            ),
        ),
    )

    surface = builder.build(rejected, surface_id=SURFACE_ID)

    assert "gratuita" not in surface.model_dump_json()


def test_the_total_comes_from_the_estimate_never_from_the_builder(builder, facts) -> None:
    """Sumar al renderizar produciría un número sin `derived_from`."""
    estimate = Estimate(
        domain="vehiculos",  # type: ignore[arg-type]
        steps=[
            EstimateStep(
                step_id="renovacion",
                title="Renovación",
                cost=Money(amount_minor=81400, currency="MXN"),
                derived_from=["fact_cost_01"],
            )
        ],
        total_cost=Money(amount_minor=81400, currency="MXN"),
        derived_from=["fact_cost_01"],
    )

    surface = builder.build(facts, surface_id=SURFACE_ID, estimate=estimate)
    data = next(m for m in surface.messages if m.update_data_model is not None)

    assert data.update_data_model.value["costos"]["total"] == "814.00 MXN"  # type: ignore[index,union-attr]


def test_money_is_formatted_from_minor_units() -> None:
    assert format_money(Money(amount_minor=125000, currency="MXN")) == "1 250.00 MXN"
    assert format_money(Money(amount_minor=0, currency="MXN")) == "0.00 MXN"


# --- Validator: los cuatro casos adversariales de §8.18 ---------------------


@pytest.mark.security
def test_a_component_outside_the_catalog_is_rejected(builder, validator, facts) -> None:
    surface = builder.build(facts, surface_id=SURFACE_ID)
    tampered = _with_component(
        surface, A2UIComponent(id="malicioso", component="ScriptTag", properties={})
    )

    result = validator.validate(tampered)

    assert not result.is_valid
    assert any(error.rule == "component_not_in_catalog" for error in result.errors)


@pytest.mark.security
def test_an_unknown_property_is_rejected(builder, validator, facts) -> None:
    """Cierra `TD-04` de Fase 0: el contrato absorbe, el catálogo cierra."""
    surface = builder.build(facts, surface_id=SURFACE_ID)
    tampered = _with_component(
        surface,
        A2UIComponent(
            id="raro", component="Text", properties={"text": "hola", "onClick": "alert(1)"}
        ),
    )

    result = validator.validate(tampered)

    assert not result.is_valid
    assert any(error.rule == "unknown_property" for error in result.errors)


@pytest.mark.security
def test_a_broken_binding_is_rejected_by_the_contract(builder, facts) -> None:
    """Un hijo inexistente no llega ni a construirse: lo rechaza `UpdateComponents`."""
    surface = builder.build(facts, surface_id=SURFACE_ID)
    tree = next(m for m in surface.messages if m.update_components is not None)
    components = list(tree.update_components.components)  # type: ignore[union-attr]
    components[0] = components[0].model_copy(update={"children": ["no_existe"]})

    with pytest.raises(ValueError, match="hijos inexistentes"):
        UpdateComponents(surface_id=SURFACE_ID, components=components)


@pytest.mark.security
def test_a_forged_action_from_another_run_is_rejected(builder, validator, facts, action) -> None:
    """`DIE-F1-105`: la acción debe pertenecer a este run, no solo existir."""
    surface = builder.build(facts, surface_id=SURFACE_ID, pending_action=action)

    result = validator.validate(surface, run_action_ids=frozenset({"act_de_otro_run"}))

    assert not result.is_valid
    assert any(error.rule == "action_not_authorised_for_run" for error in result.errors)


# --- Fixtures para el renderer (`DIE-F1-109`) -------------------------------


@pytest.mark.parametrize(
    ("filename", "action_id"),
    [
        ("cap_veh_01.jsonl", "act_fixture_veh"),
        ("cap_emp_01.jsonl", "act_fixture_emp"),
    ],
)
def test_valid_renderer_fixtures_pass_the_server_validator(
    validator: SurfaceValidator,
    filename: str,
    action_id: str,
) -> None:
    path = repository_root() / "a2ui" / "fixtures" / "citizen" / "v1" / "valid" / filename
    action = _fixture_action(action_id)
    surface = surface_from_messages(load_jsonl(path), actions=[action])

    result = validator.validate(surface, run_action_ids=frozenset({action_id}))

    assert result.is_valid, result.errors


@pytest.mark.security
@pytest.mark.parametrize(
    ("filename", "rule"),
    [
        ("component_not_allowed.jsonl", "component_not_in_catalog"),
        ("binding_not_found.jsonl", "binding_path_not_found"),
    ],
)
def test_invalid_renderer_fixtures_are_rejected(
    validator: SurfaceValidator,
    filename: str,
    rule: str,
) -> None:
    path = repository_root() / "a2ui" / "fixtures" / "citizen" / "v1" / "invalid" / filename
    surface = surface_from_messages(load_jsonl(path))

    result = validator.validate(surface)

    assert not result.is_valid
    assert rule in {error.rule for error in result.errors}


@pytest.mark.security
def test_the_forged_action_renderer_fixture_is_rejected(
    validator: SurfaceValidator,
) -> None:
    path = (
        repository_root()
        / "a2ui"
        / "fixtures"
        / "citizen"
        / "v1"
        / "invalid"
        / "forged_action.jsonl"
    )
    surface = surface_from_messages(
        load_jsonl(path),
        actions=[_fixture_action("act_other_run")],
    )

    result = validator.validate(
        surface,
        run_action_ids=frozenset({"act_expected_run"}),
    )

    assert not result.is_valid
    assert "action_not_authorised_for_run" in {error.rule for error in result.errors}


@pytest.mark.security
def test_an_action_on_a_non_interactive_component_is_rejected(
    builder, validator, facts, action
) -> None:
    """Un `Text` con acción sería un botón invisible."""
    surface = builder.build(facts, surface_id=SURFACE_ID, pending_action=action)
    tampered = _with_component(
        surface,
        A2UIComponent(
            id="trampa",
            component="Text",
            action_id=action.action_id,
            properties={"text": "inocente"},
        ),
    )

    result = validator.validate(tampered)

    assert any(error.rule == "action_on_non_interactive_component" for error in result.errors)


@pytest.mark.security
@pytest.mark.parametrize(
    "url",
    ["javascript:alert(1)", "data:text/html;base64,PHNjcmlwdD4=", "file:///etc/passwd"],
)
def test_unsafe_url_schemes_are_rejected(builder, validator, facts, url: str) -> None:
    surface = builder.build(facts, surface_id=SURFACE_ID)
    tampered = _with_component(
        surface,
        A2UIComponent(id="enlace", component="SourceList", properties={"title": "x", "url": url}),
    )

    result = validator.validate(tampered)

    assert any(error.rule == "unsafe_url_scheme" for error in result.errors)


@pytest.mark.security
def test_an_unknown_catalog_is_rejected(builder, validator, facts) -> None:
    surface = builder.build(facts, surface_id=SURFACE_ID)
    tampered = surface.model_copy(update={"catalog_id": "urn:nexo-ia:a2ui:catalog:atacante:v1"})

    result = validator.validate(tampered)

    assert not result.is_valid
    assert result.errors[0].rule == "unknown_catalog"


@pytest.mark.security
def test_validation_errors_report_the_rule_not_the_value(builder, validator, facts) -> None:
    """Un mensaje de error que incluye lo que falló filtra lo que se quería ver.

    El error nombra la propiedad no permitida —que es lo accionable— y nunca su
    valor, que es contenido bajo control de quien atacó.
    """
    surface = builder.build(facts, surface_id=SURFACE_ID)
    tampered = _with_component(
        surface,
        A2UIComponent(
            id="fuga",
            component="Text",
            properties={"text": "hola", "onload": "valor-bajo-control-del-atacante"},
        ),
    )

    result = validator.validate(tampered)

    assert not result.is_valid
    assert "valor-bajo-control-del-atacante" not in result.model_dump_json()
    assert "onload" in result.model_dump_json()


@pytest.mark.security
def test_a_property_that_looks_like_a_secret_never_reaches_the_validator(
    facts,
) -> None:
    """`SafePayload` corta una capa antes que el catálogo.

    Se descubrió al escribir la prueba anterior: el contrato rechaza la clave
    antes de que el validador la vea. Son dos barreras distintas y conviene que
    ambas queden escritas.
    """
    with pytest.raises(ValueError, match="parece un secreto"):
        A2UIComponent(
            id="fuga",
            component="Text",
            properties={"text": "hola", "api_key": "valor-sensible"},
        )


# --- Fallback (`DIE-F1-106`, `DIE-F1-107`) ----------------------------------


def test_the_web_fallback_is_never_empty(facts) -> None:
    fallback = build_fallback(facts, channel=Channel.WEB, reason="validation_failed")

    assert fallback.text
    assert "Identificación oficial vigente." in fallback.text


def test_whatsapp_gets_a_numbered_list(facts) -> None:
    fallback = build_fallback(facts, channel=Channel.WHATSAPP, reason="channel_is_text_only")

    assert fallback.numbered_items
    assert "1. " in fallback.text


def test_the_fallback_always_declares_the_mock_nature(facts) -> None:
    """`DIE-F1-096`: en el canal con menos contexto visual, con más razón."""
    fallback = build_fallback(facts, channel=Channel.WHATSAPP, reason="x")

    assert "demostración" in fallback.text


def test_a_fallback_without_evidence_refuses_to_affirm() -> None:
    empty = VerifiedFacts.empty(snapshot_id="snapshot_vacio", created_at=NOW)

    fallback = build_fallback(empty, channel=Channel.WEB, reason="no_evidence")

    assert "prefiero no afirmar nada" in fallback.text


def test_a_pending_action_produces_a_confirmation_hint(facts, action) -> None:
    fallback = build_fallback(facts, channel=Channel.WHATSAPP, reason="x", pending_action=action)

    assert fallback.action_hint is not None
    assert "CONFIRMAR" in fallback.text


def test_the_fallback_lists_its_sources(facts) -> None:
    fallback = build_fallback(facts, channel=Channel.WEB, reason="x")

    assert "src_veh_licencias" in fallback.text


# --- utilidades --------------------------------------------------------------


def _with_component(surface, component: A2UIComponent):  # type: ignore[no-untyped-def]
    """Inyecta un componente en el árbol, enlazado desde `root`.

    Simula exactamente lo que haría un atacante que controlase la salida del
    builder: un componente más, alcanzable desde la raíz.
    """
    messages = []
    for message in surface.messages:
        if message.update_components is None:
            messages.append(message)
            continue
        components = list(message.update_components.components)
        components[0] = components[0].model_copy(
            update={"children": [*components[0].children, component.id]}
        )
        messages.append(
            A2UIMessage(
                version=A2UI_PROTOCOL_VERSION,
                update_components=UpdateComponents(
                    surface_id=message.update_components.surface_id,
                    components=[*components, component],
                ),
            )
        )
    return surface.model_copy(update={"messages": messages})


def _fixture_action(action_id: str) -> A2UIAction:
    return A2UIAction(
        action_id=action_id,
        tool_name="fixtures.confirmar",
        input_schema_ref="contracts://fixtures/confirmar.input.v1",
        expected_version=1,
        requires_confirmation=True,
        label="Confirmar",
    )
