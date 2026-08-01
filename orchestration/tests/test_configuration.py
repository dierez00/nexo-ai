"""Una configuración inválida detiene el arranque (§7.8, `DIE-F0-036`).

No basta con que falle: debe decir ruta, campo y motivo. Un error de arranque
que obliga a depurar es un error de arranque que se ignora.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from nexo_contracts import ConfigurationError, ErrorCode
from nexo_orchestration.configuration import CONFIG_FILES, default_config_dir, load_config

pytestmark = pytest.mark.unit


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """Copia editable de la configuración real del repositorio."""
    source = default_config_dir()
    for filename, _ in CONFIG_FILES.values():
        (tmp_path / filename).write_text(
            (source / filename).read_text(encoding="utf-8"), encoding="utf-8"
        )
    return tmp_path


def _patch(config_dir: Path, filename: str, mutate) -> None:
    path = config_dir / filename
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def test_repository_configuration_is_valid() -> None:
    """La configuración versionada en el repo debe cargar sin tocar nada."""
    config = load_config()
    assert config.policy_version == "policies-2026-07-30"


def test_error_reports_path_field_and_reason(config_dir: Path) -> None:
    _patch(config_dir, "policies.yaml", lambda data: data.update({"version": "X"}))
    with pytest.raises(ConfigurationError) as caught:
        load_config(config_dir)
    error = caught.value
    assert "policies.yaml" in error.path
    assert error.field == "version"
    assert error.reason


def test_missing_file_is_reported(config_dir: Path) -> None:
    (config_dir / "permissions.yaml").unlink()
    with pytest.raises(ConfigurationError, match="no existe"):
        load_config(config_dir)


def test_malformed_yaml_is_reported(config_dir: Path) -> None:
    (config_dir / "catalogs.yaml").write_text("version: [sin cerrar\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="YAML mal formado"):
        load_config(config_dir)


def test_empty_file_is_reported(config_dir: Path) -> None:
    (config_dir / "catalogs.yaml").write_text("", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="vacío"):
        load_config(config_dir)


# --- Defaults que niegan (`DIE-F0-032`) --------------------------------------


def test_unknown_provider_is_rejected(config_dir: Path) -> None:
    def mutate(data: dict) -> None:
        data["aliases"][0]["provider_ref"]["provider"] = "proveedor_fantasma"

    _patch(config_dir, "model_router.yaml", mutate)
    with pytest.raises(ConfigurationError, match="allowed_providers"):
        load_config(config_dir)


def test_dangling_alias_is_rejected(config_dir: Path) -> None:
    def mutate(data: dict) -> None:
        data["policies"][0]["default_alias"] = "alias_inexistente"

    _patch(config_dir, "model_router.yaml", mutate)
    with pytest.raises(ConfigurationError, match="no existen"):
        load_config(config_dir)


def test_offline_alias_must_resolve(config_dir: Path) -> None:
    """El perfil offline es obligatorio: la demo sin red debe poder resolverlo."""
    _patch(config_dir, "model_router.yaml", lambda data: data.update({"offline_alias": "ninguno"}))
    with pytest.raises(ConfigurationError):
        load_config(config_dir)


def test_implicit_permission_is_rejected(config_dir: Path) -> None:
    _patch(config_dir, "permissions.yaml", lambda data: data.update({"default_allow": True}))
    with pytest.raises(ConfigurationError, match="default_allow"):
        load_config(config_dir)


def test_wildcard_write_permission_is_rejected(config_dir: Path) -> None:
    """Una escritura se autoriza tool por tool, nunca por dominio completo."""

    def mutate(data: dict) -> None:
        data["rules"].append(
            {
                "institution_id": "inst_demo",
                "role": "citizen",
                "domain": "vehiculos",
                "operations": ["write"],
                "allow": True,
            }
        )

    _patch(config_dir, "permissions.yaml", mutate)
    with pytest.raises(ConfigurationError, match="tool por tool"):
        load_config(config_dir)


def test_permission_for_unregistered_tool_is_rejected(config_dir: Path) -> None:
    def mutate(data: dict) -> None:
        data["rules"].append(
            {
                "institution_id": "inst_demo",
                "role": "citizen",
                "domain": "vehiculos",
                "tool": "vehiculos.tool_fantasma",
                "operations": ["read"],
                "allow": True,
            }
        )

    _patch(config_dir, "permissions.yaml", mutate)
    with pytest.raises(ConfigurationError, match="tools no registradas"):
        load_config(config_dir)


def test_unversioned_tool_is_rejected(config_dir: Path) -> None:
    def mutate(data: dict) -> None:
        data["tools"][0].pop("version")

    _patch(config_dir, "tool_registry.yaml", mutate)
    with pytest.raises(ConfigurationError):
        load_config(config_dir)


# --- Reintentos y presupuestos (`DIE-F0-034`, `DIE-F0-035`) -------------------


def test_automatic_retry_of_writes_is_rejected(config_dir: Path) -> None:
    def mutate(data: dict) -> None:
        for operation in data["operations"]:
            if operation["operation"] == "tool_write":
                operation["retry"]["max_attempts"] = 3

    _patch(config_dir, "policies.yaml", mutate)
    with pytest.raises(ConfigurationError, match="no se reintenta"):
        load_config(config_dir)


def test_retrying_unknown_outcomes_is_rejected(config_dir: Path) -> None:
    def mutate(data: dict) -> None:
        data["operations"][0]["retry"]["retry_on"].append("UNKNOWN_OUTCOME")

    _patch(config_dir, "policies.yaml", mutate)
    with pytest.raises(ConfigurationError, match="UNKNOWN_OUTCOME"):
        load_config(config_dir)


def test_agent_budget_cannot_exceed_the_run(config_dir: Path) -> None:
    def mutate(data: dict) -> None:
        data["agent_budgets"]["verifier"]["deadline_ms"] = 999_999

    _patch(config_dir, "policies.yaml", mutate)
    with pytest.raises(ConfigurationError, match="supera"):
        load_config(config_dir)


def test_outcome_categories_must_be_disjoint(config_dir: Path) -> None:
    """La reacción ante un error no puede ser ambigua (`DIE-F0-010`)."""

    def mutate(data: dict) -> None:
        data["outcomes"]["fallback_on"].append("RUN_TIMEOUT")

    _patch(config_dir, "policies.yaml", mutate)
    with pytest.raises(ConfigurationError, match="inequívoca"):
        load_config(config_dir)


def test_configuration_holds_no_secret_values() -> None:
    """`DIE-F0-033`: la configuración referencia secretos, nunca los contiene."""
    source = default_config_dir()
    for filename, _ in CONFIG_FILES.values():
        content = (source / filename).read_text(encoding="utf-8")
        for line in content.splitlines():
            stripped = line.strip()
            if "api_key" not in stripped or stripped.startswith("#"):
                continue
            assert "secret://" in stripped, (
                f"{filename} parece contener un secreto literal: {stripped!r}"
            )


def test_gemini_profile_is_pinned_and_has_no_model_fallback() -> None:
    config = load_config(model_profile="gemini")
    online = [
        entry for entry in config.model_router.aliases if entry.provider_ref.provider == "gemini"
    ]

    assert {entry.provider_ref.model for entry in online} == {"gemini-3.5-flash-lite"}
    assert {entry.alias for entry in online} == {
        "general",
        "structured_small",
        "high_accuracy",
        "judge_secondary",
    }
    assert {entry.capabilities.cost_per_1k_input_usd for entry in online} == {0.0003}
    assert {entry.capabilities.cost_per_1k_output_usd for entry in online} == {0.0025}
    assert config.policies.outcomes.fallback_on == []
    model_call = next(
        operation for operation in config.policies.operations if operation.operation == "model_call"
    )
    assert model_call.retry.max_attempts == 2
    assert ErrorCode.MODEL_OUTPUT_INVALID not in model_call.retry.retry_on
