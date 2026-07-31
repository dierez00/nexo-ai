import json
from pathlib import Path

from nexo_evaluations import EvaluationObservation, evaluate_case, load_capstone

ROOT = Path(__file__).resolve().parents[2]


def test_capstone_contains_official_paraphrase_negative_and_adversarial_cases() -> None:
    cases = load_capstone(ROOT / "evaluations/datasets/capstone_v1.jsonl")

    assert len(cases) >= 15
    assert {case.variant.value for case in cases} == {
        "official",
        "paraphrase",
        "negative",
        "adversarial",
    }
    assert len([case for case in cases if case.variant.value == "official"]) == 5


def test_frozen_official_observations_pass_the_deterministic_gate() -> None:
    cases = {
        case.case_id: case
        for case in load_capstone(ROOT / "evaluations/datasets/capstone_v1.jsonl")
    }
    observations = [
        EvaluationObservation.model_validate(json.loads(line))
        for line in (ROOT / "evaluations/baselines/core_v1_observations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    ]

    results = [evaluate_case(cases[item.case_id], item) for item in observations]

    assert len(results) == 5
    assert all(result.passed for result in results)
    assert sum(result.domain_match and result.procedure_match for result in results) >= 4


def test_new_domain_fixtures_match_the_capstone_contract() -> None:
    cases = {
        case.case_id: case
        for case in load_capstone(ROOT / "evaluations/datasets/capstone_v1.jsonl")
    }
    fixture_paths = {
        "cap_rc_01": ROOT / "domains/registro_civil/fixtures/cap_rc_01.expected.json",
        "cap_sal_01": ROOT / "domains/salud/fixtures/cap_sal_01.expected.json",
        "cap_gan_01": ROOT / "domains/ganaderia/fixtures/cap_gan_01.expected.json",
    }

    for case_id, path in fixture_paths.items():
        fixture = json.loads(path.read_text(encoding="utf-8"))
        case = cases[case_id]
        expected_tools = fixture.get("required_tools", fixture.get("required_read_tools"))

        assert fixture["domain"] == case.expected_domain.value
        assert fixture["procedure"] == case.expected_procedure
        assert fixture["max_questions"] == case.max_questions
        assert fixture["required_sources"] == case.expected_sources
        assert expected_tools == case.expected_tools
        assert fixture["required_a2ui_components"] == case.required_a2ui_components


def test_extra_tool_and_excess_questions_fail_the_gate() -> None:
    case = next(
        case
        for case in load_capstone(ROOT / "evaluations/datasets/capstone_v1.jsonl")
        if case.case_id == "cap_rc_01"
    )
    observation = EvaluationObservation(
        case_id=case.case_id,
        domain=case.expected_domain,
        procedure=case.expected_procedure,
        source_ids=case.expected_sources,
        citation_source_ids=case.expected_sources,
        selected_tools=[*case.expected_tools, "vehiculos.reservar_cita"],
        permission_compliance=False,
        a2ui_schema_valid=True,
        a2ui_components=case.required_a2ui_components,
        write_verifiable=False,
        questions_asked=2,
        catalog_version="core-catalog-2026-07-30",
    )

    result = evaluate_case(case, observation)

    assert result.passed is False
    assert result.tool_selection_correct is False
    assert result.permission_compliance is False
