"""Repositorio de tenants (solo lecturas puntuales)."""

from __future__ import annotations

from sqlalchemy import text

from nexo_api.repositories._base import load_json, read_session


async def id_by_slug(slug: str) -> int | None:
    """`id` del tenant por su slug, o ``None`` si no existe."""
    sql = text("select id from public.tenants where slug = :slug")
    async with read_session() as session:
        row = (await session.execute(sql, {"slug": slug})).mappings().first()
        return int(row["id"]) if row is not None else None


# El namespace institucional cambia solo cuando se reconfigura un tenant, así que
# se cachea en proceso: se resuelve en cada run y en cada confirmación de acción.
_institution_ref_cache: dict[int, str] = {}


async def institution_ref(tenant_id: int) -> str:
    """Namespace institucional del tenant, tal como lo nombran corpus y permisos.

    El `id` numérico del tenant y el identificador con el que se publican el
    corpus documental (`sources.yaml`) y la matriz de permisos (`permissions.yaml`)
    son cosas distintas: el primero lo asigna la base, el segundo lo asigna quien
    cura el contenido institucional. Derivar uno del otro (`inst_{id}`) hace que
    el retriever no encuentre ningún documento y que ninguna regla de permisos
    aplique, sin que nada falle de forma visible.

    Por eso el vínculo es explícito, en `tenants.metadata->>'institution_id'`. El
    fallback derivado se conserva para tenants que aún no lo declaran.
    """
    cached = _institution_ref_cache.get(tenant_id)
    if cached is not None:
        return cached

    sql = text("select metadata from public.tenants where id = :tenant_id")
    async with read_session() as session:
        row = (await session.execute(sql, {"tenant_id": tenant_id})).mappings().first()

    metadata = load_json(row["metadata"]) if row is not None else None
    declared = (metadata or {}).get("institution_id") if isinstance(metadata, dict) else None
    resolved = str(declared) if declared else f"inst_{tenant_id}"
    _institution_ref_cache[tenant_id] = resolved
    return resolved
