import pytest

from ....app.models import App
from ....product import MediaOwnerTypes

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
def media_webhook_app(db):
    """Return an app with no permissions, so each test grants what it needs."""
    return App.objects.create(name="Media webhook app", is_active=True)
