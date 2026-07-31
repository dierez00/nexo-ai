"""Redactor cerrado: sin puertos, sin cifras inventadas, con plantilla (F1.12)."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from nexo_agents.writer import PURPOSE, Writer
from nexo_contracts import (
    Audience,
    Channel,
    FactCategory,
    FactValue,
    Money,
    Profile,
    SourceCitation,
    VerificationStatus,
    VerifiedFact,
    VerifiedFacts,
)
from nexo_orchestration.testing import FakeBehavior, Scenario

pytestmark = pytest.mark.unit

NOW = datetime(2026, 7, 30, 15, 0, 0, tzinfo=UTC)

CITATION = SourceCitation(
    source_id="src_veh_licencias",
    fragment_id="frag_requisitos",
    corpus_version="vehiculos-2026-07-30",
    source_version="v3",
    valid_from=date(2026, 1, 1),
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
                "Necesitas identificación oficial vigente.",
                FactCategory.REQUIREMENT,
                items=["Identificación oficial vigente"],
            ),
            _fact(
                "fact_cost_01",
                "La renovación a tres años cuesta 814.00 MXN.",
                FactCategory.COST,
                money=Money(amount_minor=81400, currency="MXN"),
            ),
        ),
    )


def _writer(gateway_factory, scenario) -> Writer:
    return Writer(gateway=gateway_factory({PURPOSE: scenario}))


def _answer(text: str, short: str = "breve") -> Scenario:
    return Scenario(data={"answer": text, "short_answer": short})


# --- DIE-F1-094: el redactor no puede consultar nada ------------------------


def test_the_writer_has_no_rag_or_tool_ports(gateway_factory) -> None:
    """No es una regla de conducta: su constructor no los acepta."""
    writer = _writer(gateway_factory, _answer("hola"))

    attributes = set(vars(writer))
    assert not attributes & {"retriever", "tool_executor", "executor", "repository"}


def test_the_writer_constructor_rejects_a_retriever(gateway_factory) -> None:
    with pytest.raises(TypeError):
        Writer(gateway=gateway_factory({}), retriever=object())  # type: ignore[call-arg]


async def test_the_model_only_sees_accepted_facts(gateway_factory, context) -> None:
    """Enseñarle los rechazados le daría material para matizar lo descartado."""
    mixed = VerifiedFacts(
        snapshot_id="s",
        created_at=NOW,
        facts=(
            _fact(
                "fact_ok",
                "Necesitas identificación oficial vigente.",
                FactCategory.REQUIREMENT,
                items=["ID"],
            ),
            VerifiedFact(
                fact_id="fact_malo",
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
    writer = _writer(gateway_factory, _answer("Necesitas identificación oficial vigente."))

    await writer.write(mixed, context)

    block = writer._facts_block(mixed)
    assert "identificación oficial" in block
    assert "gratuita" not in block


# --- DIE-F1-098: self-check de hechos nuevos --------------------------------


@pytest.mark.security
async def test_an_invented_figure_discards_the_whole_answer(
    gateway_factory, context, facts
) -> None:
    """No se corrige el texto ni se avisa: se descarta y entra la plantilla."""
    writer = _writer(
        gateway_factory,
        _answer("El trámite cuesta 814.00 MXN y tarda 45 días hábiles."),
    )

    outcome = await writer.write(facts, context)

    assert outcome.used_template is True
    assert "45" not in outcome.answer
    assert outcome.error is not None


async def test_a_grounded_answer_survives(gateway_factory, context, facts) -> None:
    writer = _writer(
        gateway_factory,
        _answer("Necesitas identificación oficial vigente. La renovación cuesta 814.00 MXN."),
    )

    outcome = await writer.write(facts, context)

    assert outcome.used_template is False
    assert outcome.introduced_new_facts is False


async def test_reformatting_an_amount_is_not_inventing_it(gateway_factory, context, facts) -> None:
    """«814», «814.00» y «814,00» son el mismo importe; formatear no es inventar."""
    writer = _writer(gateway_factory, _answer("La renovación cuesta 814 pesos."))

    outcome = await writer.write(facts, context)

    assert outcome.used_template is False


@pytest.mark.security
async def test_an_invented_phone_number_is_caught(gateway_factory, context, facts) -> None:
    writer = _writer(
        gateway_factory,
        _answer("Llama al 618 123 4567 para más información."),
    )

    outcome = await writer.write(facts, context)

    assert outcome.used_template is True


# --- DIE-F1-099: plantilla determinista -------------------------------------


@pytest.mark.parametrize(
    "behavior", [FakeBehavior.PROVIDER_DOWN, FakeBehavior.RATE_LIMIT, FakeBehavior.TIMEOUT]
)
async def test_a_failing_model_falls_back_to_the_template(
    gateway_factory, context, facts, behavior
) -> None:
    writer = _writer(gateway_factory, Scenario(behavior=behavior))

    outcome = await writer.write(facts, context)

    assert outcome.used_template is True
    assert "identificación oficial vigente" in outcome.answer
    assert "814.00 MXN" in outcome.answer


def test_the_template_says_the_same_things_as_the_model_would(facts, gateway_factory) -> None:
    writer = _writer(gateway_factory, _answer("x"))

    template = writer.render_template(facts, channel=Channel.WEB)

    assert "Necesitas identificación oficial vigente." in template
    assert "814.00 MXN" in template
    assert "src_veh_licencias" in template


def test_the_amount_is_not_repeated_when_the_claim_already_says_it(facts, gateway_factory) -> None:
    """Repetirlo delata la plantilla sin aportar nada."""
    writer = _writer(gateway_factory, _answer("x"))

    template = writer.render_template(facts, channel=Channel.WEB)

    assert template.count("814.00 MXN") == 1


# --- DIE-F1-095, DIE-F1-096: qué debe y no debe decir -----------------------


def test_the_template_always_declares_the_mock_nature(facts, gateway_factory) -> None:
    writer = _writer(gateway_factory, _answer("x"))

    assert "demostración" in writer.render_template(facts, channel=Channel.WEB)


def test_the_template_includes_warnings_and_next_action(facts, gateway_factory) -> None:
    writer = _writer(gateway_factory, _answer("x"))

    template = writer.render_template(
        facts,
        channel=Channel.WEB,
        warnings=("Una fuente venció y se descartó.",),
        next_action="Confirma la cita para reservarla.",
    )

    assert "Una fuente venció" in template
    assert "Confirma la cita" in template


def test_without_facts_the_template_refuses_to_affirm(gateway_factory) -> None:
    writer = _writer(gateway_factory, _answer("x"))
    empty = VerifiedFacts.empty(snapshot_id="s", created_at=NOW)

    template = writer.render_template(empty, channel=Channel.WEB)

    assert "prefiero no afirmar nada" in template


# --- DIE-F1-097: versión breve para WhatsApp --------------------------------


async def test_whatsapp_gets_a_short_version_from_the_same_facts(
    gateway_factory, context, facts
) -> None:
    writer = _writer(
        gateway_factory,
        Scenario(
            data={
                "answer": "Necesitas identificación oficial vigente. Cuesta 814.00 MXN.",
                "short_answer": "",
            }
        ),
    )

    outcome = await writer.write(facts, context, channel=Channel.WHATSAPP)

    assert outcome.short_answer
    assert len(outcome.short_answer) <= 1200
    assert "814.00 MXN" in outcome.short_answer


def test_the_whatsapp_template_is_capped(facts, gateway_factory) -> None:
    writer = _writer(gateway_factory, _answer("x"))

    assert len(writer.render_template(facts, channel=Channel.WHATSAPP)) <= 1200


async def test_the_profile_reaches_the_prompt(gateway_factory, context, facts) -> None:
    writer = _writer(gateway_factory, _answer("Necesitas identificación oficial vigente."))

    await writer.write(facts, context, profile=Profile(audience=Audience.LOW_DIGITAL_LITERACY))

    assert writer.prompt is not None
    rendered = writer.prompt.render(
        audience=Audience.LOW_DIGITAL_LITERACY.value,
        locale="es-MX",
        channel="web",
        facts="x",
        warnings="x",
        next_action="x",
    )
    assert "low_digital_literacy" in rendered
