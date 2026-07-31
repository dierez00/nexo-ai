"""Esquemas del catálogo operativo (admin)."""

from __future__ import annotations

from pydantic import BaseModel


class ModuleEntry(BaseModel):
    code: str
    name: str
    is_core: bool
    enabled: bool


class RoleEntry(BaseModel):
    code: str
    name: str
    is_system: bool


class PermissionEntry(BaseModel):
    code: str
    module_code: str | None = None


class AdminCatalog(BaseModel):
    modules: list[ModuleEntry]
    roles: list[RoleEntry]
    permissions: list[PermissionEntry]
