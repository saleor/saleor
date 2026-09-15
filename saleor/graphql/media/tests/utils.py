import graphene
from django.db.models import Max

from ....media import MediaOwnerTypes
from ....media.models import ProductMedia
from ....media.utils import (
    OWNER_TYPE_TO_GRAPHQL_TYPE,
    OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE,
    OWNER_TYPE_TO_MEDIA_MODEL,
)

# Owner kinds a product media can be confused with. Parametrize cross-type tests
# over these; pairing product media with itself is not a collision.
NON_PRODUCT_OWNER_TYPES = [
    owner_type
    for owner_type in MediaOwnerTypes.ALL
    if owner_type != MediaOwnerTypes.PRODUCT
]

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
    ("App without the permission should be rejected", "app_api_client", None, False),
    (
        "App with the owner's permission should be allowed",
        "app_api_client",
        "owner",
        True,
    ),
    (
        "App with the other domain's permission should be rejected",
        "app_api_client",
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


def media_count() -> int:
    """Count media rows across every owner model."""
    return sum(model.objects.count() for model in OWNER_TYPE_TO_MEDIA_MODEL.values())


def create_colliding_media(owner_type, owner, product):
    """Create a product media and an `owner_type` media sharing one primary key.

    Every media model has its own table and its own primary key sequence, so a
    single pk names a different real row in each one. Cross-type tests are only
    meaningful when both rows exist: against an empty table a `NOT_FOUND` result
    proves nothing was there to find, not that a guard rejected the ID.

    Returns `(product_media, other_media)`. `owner_type` must not be `PRODUCT`.
    """
    shared_pk = 1 + max(
        model.objects.aggregate(max_pk=Max("pk"))["max_pk"] or 0
        for model in OWNER_TYPE_TO_MEDIA_MODEL.values()
    )
    product_media = ProductMedia.objects.create(
        pk=shared_pk, product=product, alt="product media"
    )
    other_media = OWNER_TYPE_TO_MEDIA_MODEL[owner_type].objects.create(
        pk=shared_pk, alt=f"{owner_type} media", **{owner_type: owner}
    )
    return product_media, other_media
