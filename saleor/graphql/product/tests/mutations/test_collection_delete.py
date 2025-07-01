from unittest.mock import MagicMock, patch

import pytest
from django.core.files import File
from graphql_relay import to_global_id

from .....discount.utils.promotion import get_active_catalogue_promotion_rules
from .....thumbnail.models import Thumbnail
from ....tests.utils import (
    get_graphql_content,
)

DELETE_COLLECTION_MUTATION = """
    mutation deleteCollection($id: ID!) {
        collectionDelete(id: $id) {
            collection {
                name
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.collection_deleted")
def test_delete_collection(
    deleted_webhook_mock,
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    # given
    query = DELETE_COLLECTION_MUTATION
    collection.products.set(product_list)
    collection_id = to_global_id("Collection", collection.id)
    variables = {"id": collection_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionDelete"]["collection"]
    assert data["name"] == collection.name
    with pytest.raises(collection._meta.model.DoesNotExist):
        collection.refresh_from_db()

    deleted_webhook_mock.assert_called_once()
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty is True


@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_delete_collection_with_background_image(
    delete_from_storage_task_mock,
    staff_api_client,
    collection_with_image,
    permission_manage_products,
):
    # given
    query = DELETE_COLLECTION_MUTATION
    collection = collection_with_image

    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(collection=collection, size=128, image=thumbnail_mock)
    Thumbnail.objects.create(collection=collection, size=200, image=thumbnail_mock)

    collection_id = collection.id
    variables = {"id": to_global_id("Collection", collection.id)}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionDelete"]["collection"]
    assert data["name"] == collection.name
    with pytest.raises(collection._meta.model.DoesNotExist):
        collection.refresh_from_db()
    # ensure all related thumbnails has been deleted
    assert not Thumbnail.objects.filter(collection_id=collection_id)
    assert delete_from_storage_task_mock.call_count == 3


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_delete_collection_trigger_product_updated_webhook(
    product_updated_mock,
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    query = DELETE_COLLECTION_MUTATION
    collection.products.add(*product_list)
    collection_id = to_global_id("Collection", collection.id)
    variables = {"id": collection_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionDelete"]["collection"]
    assert data["name"] == collection.name
    with pytest.raises(collection._meta.model.DoesNotExist):
        collection.refresh_from_db()
    assert len(product_list) == product_updated_mock.call_count
