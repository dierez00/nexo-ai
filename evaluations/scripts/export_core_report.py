"""Evalúa recordings congelados y exporta baseline Core JSON/Markdown."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from nexo_contracts import Domain, EvaluationReport
from nexo_evaluations import EvaluationObservation, evaluate_case, load_capstone, render_markdown


def _load_observations(path: Path) -> dict[str, EvaluationObservation]:
    observations = [
        EvaluationObservation.model_validate(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {observation.case_id: observation for observation in observations}


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    cases = load_capstone(root / "evaluations/datasets/capstone_v1.jsonl")
    official = [case for case in cases if case.variant.value == "official"]
    observations = _load_observations(root / "evaluations/baselines/core_v1_observations.jsonl")
    results = [evaluate_case(case, observations[case.case_id]) for case in official]
    report = EvaluationReport(
        report_id="eval_core_baseline_20260730",
        dataset_version="capstone_v1",
        rubric_version="deterministic-core-v1",
        corpus_versions={
            Domain.VEHICULOS: "vehiculos-2026-07-30",
            Domain.AYUNTAMIENTO_EMPRESAS: "ayuntamiento_empresas-2026-07-30",
            Domain.REGISTRO_CIVIL: "registro-civil-2026-07-30",
            Domain.SALUD: "salud-2026-07-30",
            Domain.GANADERIA: "ganaderia-2026-07-30",
        },
        config_version="core-offline-2026-07-30",
        catalog_version="core-catalog-2026-07-30",
        skill_versions={
            observation.skill_id: observation.skill_version
            for observation in observations.values()
            if observation.skill_id is not None and observation.skill_version is not None
        },
        seed=20260730,
        deterministic_results=results,
        generated_at=datetime(2026, 7, 30, 15, 0, tzinfo=UTC),
    )
    destination = root / "evaluations/reports"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "core_baseline_v1.json").write_text(
        json.dumps(
            report.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (destination / "core_baseline_v1.md").write_text(
        render_markdown(report),
        encoding="utf-8",
    )
    print(
        f"{len(results)} casos oficiales evaluados; pass rate {report.deterministic_pass_rate:.0%}"
    )


if __name__ == "__main__":
    main()
