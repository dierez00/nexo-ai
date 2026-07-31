"""Prueba: backup smoke — `supabase db dump` produce un respaldo válido y
ese respaldo se puede restaurar en una base de datos temporal reproduciendo
el mismo contenido (sección 12, "backup smoke"; checklist "Backup/restore",
sección 15).

Es un smoke test, no una prueba exhaustiva de disaster-recovery: usa el
contenedor Docker del Postgres local de Supabase (vía `docker exec` +
`psql`, que sí vienen incluidos en la imagen de Supabase aunque no estén
instalados en el host) para restaurar el dump a una base temporal y
comparar conteos de filas de una muestra de tablas. Si no encuentra el
contenedor (entorno sin Docker/Supabase local), se salta con skip en vez
de fallar — no es indicativo de un bug de la base de datos."""
import shutil
import subprocess
from pathlib import Path

import pytest

from .conftest import DATABASE_URL, new_conn

REPO_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_TABLES = ["tenants", "plans", "modules"]


def _find_db_container() -> str | None:
    if shutil.which("docker") is None:
        return None
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=supabase_db", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    names = [n for n in result.stdout.strip().splitlines() if n]
    return names[0] if names else None


@pytest.mark.integration
def test_db_dump_produces_valid_backup(tmp_path):
    dump_file = tmp_path / "backup_smoke.sql"
    result = subprocess.run(
        ["npx", "supabase", "db", "dump", "--local", "-f", str(dump_file)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        shell=True,
    )
    assert result.returncode == 0, f"supabase db dump falló:\n{result.stderr}"
    assert dump_file.exists() and dump_file.stat().st_size > 0

    content = dump_file.read_text(encoding="utf-8", errors="ignore")
    assert "CREATE TABLE" in content
    assert "public.tenants" in content


@pytest.mark.integration
def test_backup_restores_with_matching_row_counts(tmp_path):
    container = _find_db_container()
    if container is None:
        pytest.skip("no se encontró el contenedor supabase_db (Docker/Supabase local no disponible)")

    dump_file = tmp_path / "backup_restore.sql"
    dump_result = subprocess.run(
        ["npx", "supabase", "db", "dump", "--local", "-f", str(dump_file)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        shell=True,
    )
    assert dump_result.returncode == 0, f"supabase db dump falló:\n{dump_result.stderr}"

    conn = new_conn()
    try:
        original_counts = {
            t: conn.execute(f"select count(*) from public.{t}").fetchone()[0]
            for t in SAMPLE_TABLES
        }
    finally:
        conn.close()

    scratch_db = "backup_smoke_restore"
    create = subprocess.run(
        ["docker", "exec", "-i", container, "psql", "-U", "postgres", "-c",
         f"drop database if exists {scratch_db}; create database {scratch_db};"],
        capture_output=True, text=True, timeout=60,
    )
    assert create.returncode == 0, f"no se pudo crear la DB temporal:\n{create.stderr}"

    try:
        dump_sql = dump_file.read_text(encoding="utf-8")
        restore = subprocess.run(
            ["docker", "exec", "-i", container, "psql", "-U", "postgres", "-d", scratch_db],
            input=dump_sql,
            capture_output=True, text=True, timeout=120,
        )
        assert restore.returncode == 0, f"la restauración falló:\n{restore.stderr}"

        restored_counts = {}
        for table in SAMPLE_TABLES:
            check = subprocess.run(
                ["docker", "exec", "-i", container, "psql", "-U", "postgres", "-d", scratch_db,
                 "-t", "-c", f"select count(*) from public.{table}"],
                capture_output=True, text=True, timeout=30,
            )
            restored_counts[table] = int(check.stdout.strip() or "-1")

        assert restored_counts == original_counts, (
            f"conteos no coinciden tras restaurar: original={original_counts} "
            f"restaurado={restored_counts}"
        )
    finally:
        subprocess.run(
            ["docker", "exec", "-i", container, "psql", "-U", "postgres", "-c",
             f"drop database if exists {scratch_db};"],
            capture_output=True, text=True, timeout=60,
        )
