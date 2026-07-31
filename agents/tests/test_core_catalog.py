from nexo_a2ui.catalog import CITIZEN_CATALOG
from nexo_agents.catalog import CatalogLifecycle, CentralCatalog
from nexo_contracts import Domain
from nexo_mcp.authorization import PermissionMatrix
from nexo_mcp.catalog import ToolCatalog
from nexo_orchestration.configuration import load_config
from nexo_rag.corpus.cli import CORE_DOMAINS, repository_root


def _catalog() -> CentralCatalog:
    config = load_config()
    permissions = PermissionMatrix(config=config.permissions)
    tools = ToolCatalog(config=config.tool_registry, permissions=permissions)
    return CentralCatalog.load(
        repository_root(),
        domains=CORE_DOMAINS,
        tools=tools,
        models=config.model_router,
        policies=config.policies,
        a2ui_components=frozenset(component.name for component in CITIZEN_CATALOG.components),
    )


def test_the_core_catalog_resolves_all_five_domains_and_references() -> None:
    catalog = _catalog()

    assert set(catalog.manifests) == set(Domain)
    assert catalog.snapshot.version == "core-catalog-2026-07-30"
    assert catalog.snapshot.lifecycle is CatalogLifecycle.ACTIVE
    assert any(entity.entity_id == "dependency:inst_demo" for entity in catalog.snapshot.entities)


def test_skill_selection_is_versioned() -> None:
    catalog = _catalog()

    assert catalog.select_skill(Domain.SALUD, ("localizar_unidad",)) == (
        "skill_sal_navegacion",
        "1.0.0",
    )


def test_catalog_lifecycle_cannot_skip_review() -> None:
    snapshot = _catalog().snapshot.model_copy(update={"lifecycle": CatalogLifecycle.DRAFT})

    review = snapshot.transition(CatalogLifecycle.REVIEW)
    assert review.transition(CatalogLifecycle.ACTIVE).lifecycle is CatalogLifecycle.ACTIVE

    try:
        snapshot.transition(CatalogLifecycle.ACTIVE)
    except ValueError as exc:
        assert "no permitida" in str(exc)
    else:
        raise AssertionError("un catálogo draft no puede activarse sin review")
