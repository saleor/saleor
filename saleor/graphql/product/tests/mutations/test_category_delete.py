import json
from unittest.mock import MagicMock, patch

import graphene
import pytest
from django.core.files import File
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....discount.utils.promotion import get_active_catalogue_promotion_rules
from .....product.models import Category, ProductChannelListing
from .....thumbnail.models import Thumbnail
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import (
    get_graphql_content,
)

MUTATION_CATEGORY_DELETE = """
    mutation($id: ID!) {
        categoryDelete(id: $id) {
            category {
                name
            }
            errors {
                field
                message
            }
        }
    }
"""


@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_category_delete_mutation(
    delete_from_storage_task_mock,
    staff_api_client,
    category,
    product_list,
    media_root,
    permission_manage_products,
):
    # given
    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(category=category, size=128, image=thumbnail_mock)
    Thumbnail.objects.create(category=category, size=200, image=thumbnail_mock)

    category.products.add(*product_list)

    category_id = category.id

    variables = {"id": graphene.Node.to_global_id("Category", category_id)}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_DELETE, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["category"]["name"] == category.name
    with pytest.raises(category._meta.model.DoesNotExist):
        category.refresh_from_db()
    # ensure all related thumbnails has been deleted
    assert not Thumbnail.objects.filter(category_id=category_id)
    assert delete_from_storage_task_mock.call_count == 2

    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty is True


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.product.utils.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_category_delete_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    category,
    permission_manage_products,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {"id": graphene.Node.to_global_id("Category", category.id)}
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_DELETE, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["category"]["name"] == category.name

    assert not Category.objects.first()

    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": variables["id"],
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.CATEGORY_DELETED,
        [any_webhook],
        category,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )


def test_delete_category_with_background_image(
    staff_api_client,
    category_with_image,
    permission_manage_products,
    media_root,
):
    """Ensure deleting category deletes background image from storage."""
    category = category_with_image
    variables = {"id": graphene.Node.to_global_id("Category", category.id)}
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_DELETE, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["category"]["name"] == category.name
    with pytest.raises(category._meta.model.DoesNotExist):
        category.refresh_from_db()


def test_category_delete_mutation_for_categories_tree(
    staff_api_client,
    categories_tree_with_published_products,
    permission_manage_products,
):
    parent = categories_tree_with_published_products
    parent_product = parent.products.first()
    child_product = parent.children.first().products.first()

    product_list = [child_product, parent_product]

    variables = {"id": graphene.Node.to_global_id("Category", parent.id)}
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_DELETE, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["category"]["name"] == parent.name
    with pytest.raises(parent._meta.model.DoesNotExist):
        parent.refresh_from_db()

    product_channel_listings = ProductChannelListing.objects.filter(
        product__in=product_list
    )
    for product_channel_listing in product_channel_listings:
        assert product_channel_listing.is_published is False
        assert not product_channel_listing.published_at
    assert product_channel_listings.count() == 4
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty is True


def test_category_delete_mutation_for_children_from_categories_tree(
    staff_api_client,
    categories_tree_with_published_products,
    permission_manage_products,
):
    parent = categories_tree_with_published_products
    child = parent.children.first()
    parent_product = parent.products.first()
    child_product = child.products.first()

    variables = {"id": graphene.Node.to_global_id("Category", child.id)}
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_DELETE, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["category"]["name"] == child.name
    with pytest.raises(child._meta.model.DoesNotExist):
        child.refresh_from_db()

    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty is True

    parent_product.refresh_from_db()
    assert parent_product.category
    product_channel_listings = ProductChannelListing.objects.filter(
        product=parent_product
    )
    for product_channel_listing in product_channel_listings:
        assert product_channel_listing.is_published is True
        assert product_channel_listing.published_at

    child_product.refresh_from_db()
    assert not child_product.category
    product_channel_listings = ProductChannelListing.objects.filter(
        product=child_product
    )
    for product_channel_listing in product_channel_listings:
        assert product_channel_listing.is_published is False
        assert not product_channel_listing.published_at
