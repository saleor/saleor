"""READ permission model — `MANAGE_X` → `READ_X` twin registry and expansion.

The READ permission model splits the read half out of the read+write `MANAGE_*`
bundle. For every `MANAGE_X` that gates a read, a `READ_X` twin grants the *same*
read access without the write access.

Invariant: ``READ_X ⊆ MANAGE_X``. Read paths accept ``MANAGE_X OR READ_X``;
mutations stay ``MANAGE_X``-only. The expansion helper is therefore applied at the
read chokepoints only — never at ``BaseMutation.check_permissions`` — so a
``READ_X`` holder can read but can never satisfy a write.

The registry is the single, explicit source of truth. Adding a twin means one
entry here; every read chokepoint that routes through :func:`expand_read_permissions`
inherits it automatically.
"""

from collections.abc import Iterable

from .enums import AccountPermissions, BasePermissionEnum

# Explicit MANAGE -> READ registry. Keep this the single source of truth for the
# mirror set. POC scope: the account domain only (READ_USERS, READ_STAFF).
MANAGE_TO_READ_PERMISSION_MAP: dict[BasePermissionEnum, BasePermissionEnum] = {
    AccountPermissions.MANAGE_USERS: AccountPermissions.READ_USERS,
    AccountPermissions.MANAGE_STAFF: AccountPermissions.READ_STAFF,
}


def expand_read_permissions(
    permissions: Iterable[BasePermissionEnum],
) -> list[BasePermissionEnum]:
    """Return ``permissions`` widened with the READ twin of every MANAGE it contains.

    For each ``MANAGE_X`` present, append its ``READ_X`` twin so a read gated on
    ``MANAGE_X`` also accepts ``READ_X``. Nothing is ever removed, and permissions
    without a twin (auth filters, ``HANDLE_*`` action perms, …) pass through
    untouched. Call this only on read paths — mutations must keep the un-expanded
    ``MANAGE``-only list.
    """
    expanded = list(permissions)
    for perm in permissions:
        read_twin = MANAGE_TO_READ_PERMISSION_MAP.get(perm)
        if read_twin is not None and read_twin not in expanded:
            expanded.append(read_twin)
    return expanded
