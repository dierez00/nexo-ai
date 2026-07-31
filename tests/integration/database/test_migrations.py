"""Prueba: migración vacía/upgrade — las migraciones aplican limpio desde
cero y `db reset` es re-ejecutable sin errores (sección 12 del doc de Daher)."""
import subprocess
from pathlib import Path

import pytest

from .conftest import new_conn

REPO_ROOT = Path(__file__).resolve().parents[3]

EXPECTED_TABLES = {
    "tenants", "tenant_domains", "plans", "modules", "plan_modules",
    "subscriptions", "tenant_modules", "roles", "permissions",
    "role_permissions", "branches", "users", "invites", "audit_logs",
    "files", "invoices", "payments", "sources", "documents", "chunks",
    "appointments", "conversations", "messages", "runs", "run_events",
    "actions", "langgraph_checkpoints", "judge_results",
}


def _db_reset() -> subprocess.CompletedProcess:
    return subprocess.run(
        ["npx", "supabase", "db", "reset"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        shell=True,
    )


@pytest.mark.integration
def test_db_reset_is_clean_and_repeatable():
    first = _db_reset()
    assert first.returncode == 0, f"first db reset failed:\n{first.stderr}"

    second = _db_reset()
    assert second.returncode == 0, f"second db reset failed:\n{second.stderr}"


@pytest.mark.integration
def test_expected_tables_exist_after_reset():
    _db_reset()
    conn = new_conn()
    try:
        rows = conn.execute(
            "select table_name from information_schema.tables "
            "where table_schema = 'public' and table_type = 'BASE TABLE'"
        ).fetchall()
        existing = {r[0] for r in rows}
        missing = EXPECTED_TABLES - existing
        assert not missing, f"tablas esperadas faltantes tras db reset: {missing}"
    finally:
        conn.close()
