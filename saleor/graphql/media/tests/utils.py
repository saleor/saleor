import graphene

from ....product.media import (
    OWNER_TYPE_TO_GRAPHQL_TYPE,
    OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE,
)

# The auth matrix every media mutation is exercised against, per owner type.
MEDIA_AUTH_PARAMS = ("_case", "client_fixture", "permission_fixture", "is_allowed")
MEDIA_AUTH_CASES = [
    ("Unauthenticated user should be rejected", "api_client", None, False),
    ("Unprivileged user should be rejected", "user_api_client", None, False),
    (
        "Staff user without the permission should be rejected",
        "staff_api_client",
        None,
        False,
    ),
    (
        "Staff user with the owner's permission should be allowed",
        "staff_api_client",
        "owner",
        True,
    ),
    (
        "Staff user with the other domain's permission should be rejected",
        "staff_api_client",
        "other",
        False,
    ),
]


def media_global_id(owner_type, media):
    """Return the owner-typed global ID addressing a media row."""
    return graphene.Node.to_global_id(
        OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE[owner_type], media.pk
    )


def owner_global_id(owner_type, owner):
    """Return the global ID of a media owner."""
    return graphene.Node.to_global_id(OWNER_TYPE_TO_GRAPHQL_TYPE[owner_type], owner.pk)
