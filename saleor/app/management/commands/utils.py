from django.core.management import CommandError

from ....permission.enums import (
    AppPermission,
    get_permissions,
    get_permissions_enum_list,
)


def clean_permissions(required_permissions: list[str]):
    all_permissions = {perm[0]: perm[1] for perm in get_permissions_enum_list()}
    for perm in required_permissions:
        if not all_permissions.get(perm):
            raise CommandError(
                f"Permission: {perm} doesn't exist in Saleor."
                f" Available permissions: {all_permissions}"
            )
    # Enforce the same invariant that GraphQL mutations enforce. CLI commands
    # bypass the GraphQL layer entirely, so without this guard
    # `manage.py create_app foo --permission MANAGE_APPS` would silently produce
    # an app that can manage other apps - a privilege-laundering primitive.
    manage_apps = AppPermission.MANAGE_APPS.name
    if manage_apps in required_permissions:
        raise CommandError(f"Permission(s) cannot be granted to an app: {manage_apps}.")
    permissions = get_permissions(
        [all_permissions[perm] for perm in required_permissions]
    )
    return permissions
