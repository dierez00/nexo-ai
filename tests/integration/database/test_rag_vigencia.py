"""Prueba: vigencia RAG — `match_chunks` filtra por institución, dominio y
vigencia de la fuente (status='active' y valid_to > now()), tal como exige
el criterio de aceptación "RAG filtra dominio/institución/vigencia"
(sección 13) y la sección 12 ("vigencia RAG")."""
import pytest

from .conftest import cleanup_tenant, make_tenant

DIM = 1536


def _vec(value: float) -> str:
    return "[" + ",".join([str(value)] * DIM) + "]"


def _make_source(conn, tenant_id, domain, checksum, status="active", valid_to=None):
    row = conn.execute(
        "insert into public.sources (tenant_id, domain, name, checksum, status, valid_to) "
        "values (%s, %s, %s, %s, %s, %s) returning id",
        (tenant_id, domain, f"source-{checksum}", checksum, status, valid_to),
    ).fetchone()
    return row[0]


def _make_document(conn, tenant_id, source_id, title):
    row = conn.execute(
        "insert into public.documents (tenant_id, source_id, title) "
        "values (%s, %s, %s) returning id",
        (tenant_id, source_id, title),
    ).fetchone()
    return row[0]


def _make_chunk(conn, tenant_id, document_id, domain, content, embedding_value):
    conn.execute(
        "insert into public.chunks (tenant_id, document_id, domain, content, embedding) "
        "values (%s, %s, %s, %s, %s::vector(1536))",
        (tenant_id, document_id, domain, content, _vec(embedding_value)),
    )


@pytest.fixture
def tenant(admin_conn):
    tid = make_tenant(admin_conn)
    yield tid
    cleanup_tenant(admin_conn, tid)


@pytest.mark.integration
def test_match_chunks_excludes_expired_source(admin_conn, tenant):
    valid_source = _make_source(admin_conn, tenant, "vehiculos", "chk-valid", status="active")
    valid_doc = _make_document(admin_conn, tenant, valid_source, "doc-valid")
    _make_chunk(admin_conn, tenant, valid_doc, "vehiculos", "contenido vigente", 0.1)

    expired_source = _make_source(
        admin_conn, tenant, "vehiculos", "chk-expired", status="expired"
    )
    expired_doc = _make_document(admin_conn, tenant, expired_source, "doc-expired")
    _make_chunk(admin_conn, tenant, expired_doc, "vehiculos", "contenido vencido", 0.1)

    rows = admin_conn.execute(
        "select content from public.match_chunks("
        "query_embedding := %s::vector(1536), match_threshold := 0.0, "
        "match_count := 10, filter_domain := null, filter_tenant_id := %s)",
        (_vec(0.1), tenant),
    ).fetchall()

    contents = {r[0] for r in rows}
    assert "contenido vigente" in contents
    assert "contenido vencido" not in contents


@pytest.mark.integration
def test_match_chunks_excludes_past_valid_to(admin_conn, tenant):
    past_source = _make_source(
        admin_conn, tenant, "vehiculos", "chk-past", status="active",
        valid_to="2020-01-01T00:00:00Z",
    )
    past_doc = _make_document(admin_conn, tenant, past_source, "doc-past")
    _make_chunk(admin_conn, tenant, past_doc, "vehiculos", "vencido por fecha", 0.1)

    rows = admin_conn.execute(
        "select content from public.match_chunks("
        "query_embedding := %s::vector(1536), match_threshold := 0.0, "
        "match_count := 10, filter_domain := null, filter_tenant_id := %s)",
        (_vec(0.1), tenant),
    ).fetchall()

    assert not any(r[0] == "vencido por fecha" for r in rows)


@pytest.mark.integration
def test_match_chunks_filters_by_domain_and_tenant(admin_conn, tenant):
    other_tenant = make_tenant(admin_conn)
    try:
        source = _make_source(admin_conn, tenant, "salud", "chk-domain")
        doc = _make_document(admin_conn, tenant, source, "doc-domain")
        _make_chunk(admin_conn, tenant, doc, "salud", "contenido de salud", 0.1)

        other_source = _make_source(admin_conn, other_tenant, "vehiculos", "chk-other")
        other_doc = _make_document(admin_conn, other_tenant, other_source, "doc-other")
        _make_chunk(admin_conn, other_tenant, other_doc, "vehiculos", "otro tenant", 0.1)

        rows = admin_conn.execute(
            "select content from public.match_chunks("
            "query_embedding := %s::vector(1536), match_threshold := 0.0, "
            "match_count := 10, filter_domain := 'vehiculos', filter_tenant_id := %s)",
            (_vec(0.1), tenant),
        ).fetchall()

        contents = {r[0] for r in rows}
        assert "contenido de salud" not in contents, "el filtro de dominio debe excluirlo"
        assert "otro tenant" not in contents, "el filtro de tenant debe excluirlo"
    finally:
        cleanup_tenant(admin_conn, other_tenant)
