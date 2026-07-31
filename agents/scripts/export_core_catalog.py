"""Exporta el catálogo central Core para consumidores y fixtures web."""

from __future__ import annotations

import json

from nexo_a2ui.catalog import CITIZEN_CATALOG
from nexo_agents.catalog import CentralCatalog
from nexo_mcp.authorization import PermissionMatrix
from nexo_mcp.catalog import ToolCatalog
from nexo_orchestration.configuration import load_config
from nexo_rag.corpus.cli import CORE_DOMAINS, repository_root


def main() -> None:
    root = repository_root()
    config = load_config()
    permissions = PermissionMatrix(config=config.permissions)
    tools = ToolCatalog(config=config.tool_registry, permissions=permissions)
    catalog = CentralCatalog.load(
        root,
        domains=CORE_DOMAINS,
        tools=tools,
        models=config.model_router,
        policies=config.policies,
        a2ui_components=frozenset(component.name for component in CITIZEN_CATALOG.components),
    )
    rendered = (
        json.dumps(
            catalog.snapshot.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    )
    destinations = (
        root / "agents/catalogs/core/v1/catalog.json",
        root / "apps/web/public/fixtures/catalog/core.json",
    )
    for destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8")
    print(f"{len(destinations)} catálogos exportados")


if __name__ == "__main__":
    main()
