import pytest

from ....app.models import App
from ....product import MediaOwnerTypes
from ....product.media import MEDIA_OWNER_PERMISSION_MAP

OWNER_TYPE_TO_FIXTURE = {
    MediaOwnerTypes.PRODUCT: "product",
    MediaOwnerTypes.CATEGORY: "category",
    MediaOwnerTypes.COLLECTION: "published_collection",
    MediaOwnerTypes.PAGE: "page",
}


@pytest.fixture
def media_owner(request, owner_type):
    """Return the owner instance matching the test's `owner_type` parameter."""
    return request.getfixturevalue(OWNER_TYPE_TO_FIXTURE[owner_type])


@pytest.fixture
def grant_media_permission(request, owner_type):
    """Grant a client the permission named by a `MEDIA_AUTH_CASES` row.

    `"owner"` grants the permission governing the test's owner type, `"other"`
    grants one from the other domain, and `None` grants nothing.
    """

    def grant(client, permission_fixture):
        if not permission_fixture:
            return
        owner_permission = MEDIA_OWNER_PERMISSION_MAP[owner_type]
        other_permission = next(
            permission
            for permission in MEDIA_OWNER_PERMISSION_MAP.values()
            if permission != owner_permission
        )
        permission = {"owner": owner_permission, "other": other_permission}[
            permission_fixture
        ]
        perm_object = request.getfixturevalue(f"permission_{permission.codename}")
        assert perm_object.content_type.app_label == permission.app_label
        if client.user:
            client.user.user_permissions.add(perm_object)

    return grant


@pytest.fixture
def media_webhook_app(db):
    """Return an app with no permissions, so each test grants what it needs."""
    return App.objects.create(name="Media webhook app", is_active=True)
