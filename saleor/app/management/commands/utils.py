import json
from argparse import ArgumentTypeError
from typing import Any

from django.core.management import BaseCommand, CommandError
from graphql import GraphQLError

# Special case: non-GraphQL code must not import from the graphql layer, but
# these commands accept GraphQL global IDs as input, so they reuse the same
# decoder the API uses.
from ....graphql.core.utils import from_global_id_or_error
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


def parse_bool(value: str) -> bool:
    """Parse a strict `true`/`false` command-line value."""
    match value.lower():
        case "true":
            return True
        case "false":
            return False
    raise ArgumentTypeError(f"expected 'true' or 'false', got {value!r}")


def parse_id(value: str, expected_type: str) -> int:
    """Parse a database ID or a GraphQL global ID of `expected_type`."""
    try:
        return int(value)
    except ValueError:
        pass
    try:
        _, pk = from_global_id_or_error(value, expected_type, raise_error=True)
    except GraphQLError as e:
        raise CommandError(e.message) from e
    try:
        return int(pk)
    except ValueError as e:
        raise CommandError(f"Invalid ID: {value}. Expected: {expected_type}.") from e


class JSONLinesCommand(BaseCommand):
    """Command that writes its output as JSON Lines for machine consumption."""

    def _write(self, record: dict[str, Any]) -> None:
        self.stdout.write(json.dumps(record))
