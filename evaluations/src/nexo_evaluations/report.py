"""Render Markdown comparable del reporte de evaluación Core."""

from __future__ import annotations

from nexo_contracts import EvaluationReport


def _mark(value: bool) -> str:
    return "✓" if value else "✗"


def render_markdown(report: EvaluationReport) -> str:
    passed = sum(result.passed for result in report.deterministic_results)
    total = len(report.deterministic_results)
    lines = [
        "# Baseline Core",
        "",
        f"- Reporte: `{report.report_id}`",
        f"- Dataset: `{report.dataset_version}`",
        f"- Catálogo: `{report.catalog_version}`",
        f"- Configuración: `{report.config_version}`",
        f"- Resultado: **{passed}/{total}** ({report.deterministic_pass_rate:.0%})",
        "",
        "## Casos",
        "",
        "| Caso | Dominio | Trámite | Fuentes | Citas | Tools | Permisos | A2UI | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in report.deterministic_results:
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{result.case_id}`",
                    _mark(result.domain_match),
                    _mark(result.procedure_match),
                    f"{result.source_coverage:.0%}",
                    f"{result.citation_precision:.0%}",
                    _mark(result.tool_selection_correct),
                    _mark(result.permission_compliance),
                    _mark(result.a2ui_schema_valid),
                    _mark(result.passed),
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Versiones de corpus",
            "",
            *[
                f"- `{domain.value}`: `{version}`"
                for domain, version in sorted(
                    report.corpus_versions.items(), key=lambda item: item[0].value
                )
            ],
            "",
            "## Skills",
            "",
            *[
                f"- `{skill}`: `{version}`"
                for skill, version in sorted(report.skill_versions.items())
            ],
            "",
        ]
    )
    return "\n".join(lines)


__all__ = ["render_markdown"]
