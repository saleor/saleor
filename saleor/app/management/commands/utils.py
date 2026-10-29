from argparse import ArgumentTypeError

import graphene
from django.core.management import CommandError

from ....permission.enums import get_permissions, get_permissions_enum_list


def clean_permissions(required_permissions: list[str]):
    all_permissions = {perm[0]: perm[1] for perm in get_permissions_enum_list()}
    for perm in required_permissions:
        if not all_permissions.get(perm):
            raise CommandError(
                f"Permission: {perm} doesn't exist in Saleor."
                f" Available permissions: {all_permissions}"
            )
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


def decode_global_id(global_id: str, expected_type: str) -> int:
    try:
        type_, pk = graphene.Node.from_global_id(global_id)
        pk = int(pk)
    except ValueError as e:
        raise CommandError(f"Invalid ID: {global_id}.") from e
    if type_ != expected_type:
        raise CommandError(
            f"Invalid ID: {global_id}. Expected: {expected_type}, received: {type_}."
        )
    return pk
