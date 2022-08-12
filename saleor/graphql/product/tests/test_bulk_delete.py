from unittest.mock import MagicMock, patch

import graphene
import pytest
from django.core.files import File
from django.utils import timezone
from prices import Money, TaxedMoney

from ....attribute.models import AttributeValue
from ....attribute.utils import associate_attribute_values_to_instance
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import add_variant_to_checkout, calculate_checkout_quantity
from ....order import OrderEvents, OrderStatus
from ....order.models import OrderEvent, OrderLine
from ....plugins.manager import get_plugins_manager
from ....product import ProductTypeKind
from ....product.error_codes import ProductErrorCode
from ....product.models import (
    Category,
    Collection,
    Product,
    ProductChannelListing,
    ProductMedia,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
    VariantMedia,
)
from ....tests.utils import flush_post_commit_hooks
from ....thumbnail.models import Thumbnail
from ...tests.utils import get_graphql_content


@pytest.fixture
def category_list():
    category_1 = Category.objects.create(name="Category 1", slug="category-1")
    category_2 = Category.objects.create(name="Category 2", slug="category-2")
    category_3 = Category.objects.create(name="Category 3", slug="category-3")
    return category_1, category_2, category_3


@pytest.fixture
def product_type_list():
    product_type_1 = ProductType.objects.create(
        name="Type 1", slug="type-1", kind=ProductTypeKind.NORMAL
    )
    product_type_2 = ProductType.objects.create(
        name="Type 2", slug="type-2", kind=ProductTypeKind.NORMAL
    )
    product_type_3 = ProductType.objects.create(
        name="Type 3", slug="type-3", kind=ProductTypeKind.NORMAL
    )
    return product_type_1, product_type_2, product_type_3


MUTATION_CATEGORY_BULK_DELETE = """
    mutation categoryBulkDelete($ids: [ID!]!) {
        categoryBulkDelete(ids: $ids) {
            count
        }
    }
"""


def test_delete_categories(staff_api_client, category_list, permission_manage_products):
    variables = {
        "ids": [
            graphene.Node.to_global_id("Category", category.id)
            for category in category_list
        ]
    }
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_BULK_DELETE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    assert content["data"]["categoryBulkDelete"]["count"] == 3
    assert not Category.objects.filter(
        id__in=[category.id for category in category_list]
    ).exists()


@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_categories_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    category_list,
    permission_manage_products,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {
        "ids": [
            graphene.Node.to_global_id("Category", category.id)
            for category in category_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_BULK_DELETE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["categoryBulkDelete"]["count"] == 3
    assert mocked_webhook_trigger.call_count == len(category_list)


def test_delete_categories_with_images(
    staff_api_client,
    category_list,
    image_list,
    permission_manage_products,
    media_root,
):
    category_list[0].background_image = image_list[0]
    category_list[0].save(update_fields=["background_image"])

    category_list[1].background_image = image_list[1]
    category_list[1].save(update_fields=["background_image"])

    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.bulk_create(
        [
            Thumbnail(category=category_list[0], size=128, image=thumbnail_mock),
            Thumbnail(category=category_list[1], size=128, image=thumbnail_mock),
        ]
    )

    variables = {
        "ids": [
            graphene.Node.to_global_id("Category", category.id)
            for category in category_list
        ]
    }
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_BULK_DELETE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    assert content["data"]["categoryBulkDelete"]["count"] == 3
    assert not Category.objects.filter(
        id__in=[category.id for category in category_list]
    ).exists()
    # ensure corresponding thumbnails has been deleted
    assert not Thumbnail.objects.all()


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_delete_categories_trigger_product_updated_webhook(
    product_updated_mock,
    staff_api_client,
    category_list,
    product_list,
    permission_manage_products,
):
    first_product = product_list[0]
    first_product.category = category_list[0]
    first_product.save()

    second_product = product_list[1]
    second_product.category = category_list[1]
    second_product.save()

    variables = {
        "ids": [
            graphene.Node.to_global_id("Category", category.id)
            for category in category_list
        ]
    }
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_BULK_DELETE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    assert content["data"]["categoryBulkDelete"]["count"] == 3
    assert not Category.objects.filter(
        id__in=[category.id for category in category_list]
    ).exists()

    # updated two categories with products
    assert product_updated_mock.call_count == 2


@patch("saleor.product.utils.update_products_discounted_prices_task")
def test_delete_categories_with_subcategories_and_products(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    category_list,
    permission_manage_products,
    product,
    category,
    channel_USD,
    channel_PLN,
):
    product.category = category
    category.parent = category_list[0]
    category.save()

    parent_product = Product.objects.get(pk=product.pk)
    parent_product.slug = "parent-product"
    parent_product.id = None
    parent_product.category = category_list[0]
    parent_product.save()

    ProductChannelListing.objects.bulk_create(
        [
            ProductChannelListing(
                product=parent_product, channel=channel_USD, is_published=True
            ),
            ProductChannelListing(
                product=parent_product,
                channel=channel_PLN,
                is_published=True,
                published_at=timezone.now(),
            ),
        ]
    )

    product_list = [product, parent_product]

    variables = {
        "ids": [
            graphene.Node.to_global_id("Category", category.id)
            for category in category_list
        ]
    }
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_BULK_DELETE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    assert content["data"]["categoryBulkDelete"]["count"] == 3
    assert not Category.objects.filter(
        id__in=[category.id for category in category_list]
    ).exists()

    mock_update_products_discounted_prices_task.delay.assert_called_once()
    (
        _call_args,
        call_kwargs,
    ) = mock_update_products_discounted_prices_task.delay.call_args

    assert set(call_kwargs["product_ids"]) == set([p.pk for p in product_list])

    for product in product_list:
        product.refresh_from_db()
        assert not product.category

    product_channel_listings = ProductChannelListing.objects.filter(
        product__in=product_list
    )
    for product_channel_listing in product_channel_listings:
        assert product_channel_listing.is_published is False
        assert not product_channel_listing.published_at
    assert product_channel_listings.count() == 3


MUTATION_COLLECTION_BULK_DELETE = """
    mutation collectionBulkDelete($ids: [ID!]!) {
        collectionBulkDelete(ids: $ids) {
            count
        }
    }
"""


def test_delete_collections(
    staff_api_client, collection_list, permission_manage_products
):
    query = MUTATION_COLLECTION_BULK_DELETE

    variables = {
        "ids": [
            graphene.Node.to_global_id("Collection", collection.id)
            for collection in collection_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["collectionBulkDelete"]["count"] == 3
    assert not Collection.objects.filter(
        id__in=[collection.id for collection in collection_list]
    ).exists()


def test_delete_collections_with_images(
    staff_api_client,
    collection_list,
    image_list,
    permission_manage_products,
    media_root,
):
    query = MUTATION_COLLECTION_BULK_DELETE

    collection_list[0].background_image = image_list[0]
    collection_list[0].save(update_fields=["background_image"])

    collection_list[1].background_image = image_list[1]
    collection_list[1].save(update_fields=["background_image"])

    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.bulk_create(
        [
            Thumbnail(collection=collection_list[0], size=128, image=thumbnail_mock),
            Thumbnail(collection=collection_list[1], size=128, image=thumbnail_mock),
        ]
    )

    variables = {
        "ids": [
            graphene.Node.to_global_id("Collection", collection.id)
            for collection in collection_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["collectionBulkDelete"]["count"] == 3
    assert not Collection.objects.filter(
        id__in=[collection.id for collection in collection_list]
    ).exists()
    # ensure corresponding thumbnails has been deleted
    assert not Thumbnail.objects.all()


@patch("saleor.plugins.manager.PluginsManager.collection_deleted")
def test_delete_collections_trigger_collection_deleted_webhook(
    collection_deleted_mock,
    staff_api_client,
    collection_list,
    permission_manage_products,
):
    variables = {
        "ids": [
            graphene.Node.to_global_id("Collection", collection.id)
            for collection in collection_list
        ]
    }
    response = staff_api_client.post_graphql(
        MUTATION_COLLECTION_BULK_DELETE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    assert content["data"]["collectionBulkDelete"]["count"] == 3
    assert not Collection.objects.filter(
        id__in=[collection.id for collection in collection_list]
    ).exists()
    assert len(collection_list) == collection_deleted_mock.call_count


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_delete_collections_trigger_product_updated_webhook(
    product_updated_mock,
    staff_api_client,
    collection_list,
    product_list,
    permission_manage_products,
):
    for collection in collection_list:
        collection.products.add(*product_list)
    variables = {
        "ids": [
            graphene.Node.to_global_id("Collection", collection.id)
            for collection in collection_list
        ]
    }
    response = staff_api_client.post_graphql(
        MUTATION_COLLECTION_BULK_DELETE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    assert content["data"]["collectionBulkDelete"]["count"] == 3
    assert not Collection.objects.filter(
        id__in=[collection.id for collection in collection_list]
    ).exists()
    assert len(product_list) == product_updated_mock.call_count


DELETE_PRODUCTS_MUTATION = """
mutation productBulkDelete($ids: [ID!]!) {
    productBulkDelete(ids: $ids) {
        count
        errors {
            code
            field
        }
    }
}
"""


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_products(
    mocked_recalculate_orders_task,
    staff_api_client,
    product_list,
    permission_manage_products,
    order_list,
    channel_USD,
):
    # given
    query = DELETE_PRODUCTS_MUTATION

    not_draft_order = order_list[0]
    draft_order = order_list[1]
    draft_order.status = OrderStatus.DRAFT
    draft_order.save(update_fields=["status"])

    draft_order_lines_pks = []
    not_draft_order_lines_pks = []
    for variant in [product_list[0].variants.first(), product_list[1].variants.first()]:
        product = variant.product
        variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
        net = variant.get_price(product, [], channel_USD, variant_channel_listing, None)
        gross = Money(amount=net.amount, currency=net.currency)
        quantity = 3
        total_price = TaxedMoney(net=net * quantity, gross=gross * quantity)
        order_line = OrderLine.objects.create(
            variant=variant,
            order=draft_order,
            product_name=str(product),
            variant_name=str(variant),
            product_sku=variant.sku,
            product_variant_id=variant.get_global_id(),
            is_shipping_required=variant.is_shipping_required(),
            is_gift_card=variant.is_gift_card(),
            unit_price=TaxedMoney(net=net, gross=gross),
            total_price=total_price,
            quantity=3,
        )
        draft_order_lines_pks.append(order_line.pk)

        order_line_not_draft = OrderLine.objects.create(
            variant=variant,
            order=not_draft_order,
            product_name=str(product),
            variant_name=str(variant),
            product_sku=variant.sku,
            product_variant_id=variant.get_global_id(),
            is_shipping_required=variant.is_shipping_required(),
            is_gift_card=variant.is_gift_card(),
            unit_price=TaxedMoney(net=net, gross=gross),
            total_price=total_price,
            quantity=3,
        )
        not_draft_order_lines_pks.append(order_line_not_draft.pk)

    variables = {
        "ids": [
            graphene.Node.to_global_id("Product", product.id)
            for product in product_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["productBulkDelete"]["count"] == 3
    assert not Product.objects.filter(
        id__in=[product.id for product in product_list]
    ).exists()

    assert not OrderLine.objects.filter(pk__in=draft_order_lines_pks).exists()

    assert OrderLine.objects.filter(pk__in=not_draft_order_lines_pks).exists()
    mocked_recalculate_orders_task.assert_called_once_with([draft_order.id])


def test_delete_products_invalid_object_typed_of_given_ids(
    staff_api_client, product_list, permission_manage_products, staff_user
):
    query = DELETE_PRODUCTS_MUTATION
    staff_user.user_permissions.add(permission_manage_products)

    variables = {
        "ids": [
            graphene.Node.to_global_id("PageType", type.id) for type in product_list
        ]
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productBulkDelete"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.GRAPHQL_ERROR.name
    assert errors[0]["field"] == "ids"
    assert data["count"] == 0


@patch("saleor.product.signals.delete_from_storage_task.delay")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_products_with_images(
    mocked_recalculate_orders_task,
    delete_from_storage_task_mock,
    staff_api_client,
    product_list,
    image_list,
    permission_manage_products,
    channel_USD,
    media_root,
):
    # given
    media1 = ProductMedia.objects.create(product=product_list[0], image=image_list[0])
    media2 = ProductMedia.objects.create(product=product_list[1], image=image_list[1])

    query = DELETE_PRODUCTS_MUTATION
    variables = {
        "ids": [
            graphene.Node.to_global_id("Product", product.id)
            for product in product_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["productBulkDelete"]["count"] == 3
    assert delete_from_storage_task_mock.call_count == 2
    assert {
        call_args.args[0] for call_args in delete_from_storage_task_mock.call_args_list
    } == {media1.image.path, media2.image.path}
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_products_trigger_webhook(
    mocked_recalculate_orders_task,
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    product_list,
    permission_manage_products,
    channel_USD,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    query = DELETE_PRODUCTS_MUTATION
    variables = {
        "ids": [
            graphene.Node.to_global_id("Product", product.id)
            for product in product_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["productBulkDelete"]["count"] == 3
    assert mocked_webhook_trigger.called
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_products_without_variants(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    product_list,
    permission_manage_products,
    channel_USD,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    for product in product_list:
        product.variants.all().delete()

    query = DELETE_PRODUCTS_MUTATION
    variables = {
        "ids": [
            graphene.Node.to_global_id("Product", product.id)
            for product in product_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["productBulkDelete"]["count"] == 3
    assert mocked_webhook_trigger.called


def test_delete_products_removes_checkout_lines(
    staff_api_client,
    product_list,
    checkout_with_items,
    permission_manage_products,
    channel_USD,
    settings,
):
    # given
    checkout = checkout_with_items
    lines_count = checkout.lines.count()
    lines, _ = fetch_checkout_lines(checkout)
    old_quantity = calculate_checkout_quantity(lines)

    query = DELETE_PRODUCTS_MUTATION
    variables = {
        "ids": [
            graphene.Node.to_global_id("Product", product.id)
            for product in product_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["productBulkDelete"]["count"] == 3

    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == lines_count - 3
    assert old_quantity == calculate_checkout_quantity(lines) + 3


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_products_with_file_attributes(
    mocked_recalculate_orders_task,
    staff_api_client,
    product_list,
    file_attribute,
    permission_manage_products,
    channel_USD,
    settings,
):
    # given
    query = DELETE_PRODUCTS_MUTATION

    values = [value for value in file_attribute.values.all()]
    for i, product in enumerate(product_list[: len(values)]):
        product_type = product.product_type
        product_type.product_attributes.add(file_attribute)
        existing_value = values[i]
        associate_attribute_values_to_instance(product, file_attribute, existing_value)

    variables = {
        "ids": [
            graphene.Node.to_global_id("Product", product.id)
            for product in product_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["productBulkDelete"]["count"] == 3
    mocked_recalculate_orders_task.assert_not_called()
    for value in values:
        with pytest.raises(value._meta.model.DoesNotExist):
            value.refresh_from_db()


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_products_variants_in_draft_order(
    mocked_recalculate_orders_task,
    draft_order,
    staff_api_client,
    product_list,
    permission_manage_products,
):
    query = DELETE_PRODUCTS_MUTATION
    products_id = draft_order.lines.all().values_list("variant__product_id", flat=True)
    assert ProductChannelListing.objects.filter(product_id__in=products_id).exists()

    variables = {
        "ids": [
            graphene.Node.to_global_id("Product", product_id)
            for product_id in products_id
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["productBulkDelete"]["count"] == 2
    assert not Product.objects.filter(id__in=products_id).exists()
    assert not ProductChannelListing.objects.filter(product_id__in=products_id).exists()
    mocked_recalculate_orders_task.assert_called_once_with([draft_order.id])

    event = OrderEvent.objects.filter(
        type=OrderEvents.ORDER_LINE_PRODUCT_DELETED
    ).last()
    assert event
    assert event.order == draft_order
    assert event.user == staff_api_client.user
    expected_params = [
        {
            "item": str(line),
            "line_pk": line.pk,
            "quantity": line.quantity,
        }
        for line in draft_order.lines.all()
    ]
    for param in expected_params:
        assert param in event.parameters


def test_delete_product_media(
    staff_api_client, product_with_images, permission_manage_products
):
    media = product_with_images.media.all()

    query = """
    mutation productMediaBulkDelete($ids: [ID!]!) {
        productMediaBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductMedia", media_obj.id)
            for media_obj in media
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["productMediaBulkDelete"]["count"] == 2
    assert not ProductMedia.objects.filter(
        id__in=[media_obj.id for media_obj in media]
    ).exists()


PRODUCT_TYPE_BULK_DELETE_MUTATION = """
    mutation productTypeBulkDelete($ids: [ID!]!) {
        productTypeBulkDelete(ids: $ids) {
            count
            errors {
                field
                code
            }
        }
    }
"""


def test_delete_product_types(
    staff_api_client, product_type_list, permission_manage_product_types_and_attributes
):
    query = PRODUCT_TYPE_BULK_DELETE_MUTATION

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductType", type.id)
            for type in product_type_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)

    assert content["data"]["productTypeBulkDelete"]["count"] == 3
    assert not ProductType.objects.filter(
        id__in=[type.id for type in product_type_list]
    ).exists()


def test_delete_product_types_invalid_object_typed_of_given_ids(
    staff_api_client,
    product_type_list,
    permission_manage_product_types_and_attributes,
    staff_user,
):
    query = PRODUCT_TYPE_BULK_DELETE_MUTATION
    staff_user.user_permissions.add(permission_manage_product_types_and_attributes)

    variables = {
        "ids": [
            graphene.Node.to_global_id("PageType", type.id)
            for type in product_type_list
        ]
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productTypeBulkDelete"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.GRAPHQL_ERROR.name
    assert errors[0]["field"] == "ids"
    assert data["count"] == 0


def test_delete_product_types_with_file_attributes(
    staff_api_client,
    product_type_list,
    product_list,
    file_attribute,
    permission_manage_product_types_and_attributes,
):
    query = PRODUCT_TYPE_BULK_DELETE_MUTATION

    values = [value for value in file_attribute.values.all()]
    for i, product_type in enumerate(product_type_list[: len(values)]):
        product_type.product_attributes.add(file_attribute)
        product = product_list[i]
        product.product_type = product_type
        product.save()
        existing_value = values[i]
        associate_attribute_values_to_instance(product, file_attribute, existing_value)

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductType", type.id)
            for type in product_type_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)

    assert content["data"]["productTypeBulkDelete"]["count"] == 3
    assert not ProductType.objects.filter(
        id__in=[type.id for type in product_type_list]
    ).exists()
    for value in values:
        with pytest.raises(value._meta.model.DoesNotExist):
            value.refresh_from_db()


PRODUCT_VARIANT_BULK_DELETE_MUTATION = """
mutation productVariantBulkDelete($ids: [ID!]!) {
    productVariantBulkDelete(ids: $ids) {
        count
        errors {
            code
            field
        }
    }
}
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_deleted")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_variants(
    mocked_recalculate_orders_task,
    product_variant_deleted_webhook_mock,
    staff_api_client,
    product_variant_list,
    permission_manage_products,
):
    query = PRODUCT_VARIANT_BULK_DELETE_MUTATION

    product = product_variant_list[0].product

    variant = product.variants.get(sku="123")
    variant.sku = "abcd"
    variant.save(update_fields=["sku"])

    assert ProductVariantChannelListing.objects.filter(
        variant_id__in=[variant.id for variant in product_variant_list]
    ).exists()

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductVariant", variant.id)
            for variant in product_variant_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()

    assert content["data"]["productVariantBulkDelete"]["count"] == 4
    assert not ProductVariant.objects.filter(
        id__in=[variant.id for variant in product_variant_list]
    ).exists()
    assert (
        product_variant_deleted_webhook_mock.call_count
        == content["data"]["productVariantBulkDelete"]["count"]
    )
    mocked_recalculate_orders_task.assert_not_called()


def test_delete_product_variants_invalid_object_typed_of_given_ids(
    staff_api_client, product_variant_list, permission_manage_products, staff_user
):
    query = PRODUCT_VARIANT_BULK_DELETE_MUTATION
    staff_user.user_permissions.add(permission_manage_products)

    variables = {
        "ids": [
            graphene.Node.to_global_id("PageType", type.id)
            for type in product_variant_list
        ]
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkDelete"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.GRAPHQL_ERROR.name
    assert errors[0]["field"] == "ids"
    assert data["count"] == 0


def test_delete_product_variants_removes_checkout_lines(
    staff_api_client,
    checkout,
    product_list,
    permission_manage_products,
):
    query = PRODUCT_VARIANT_BULK_DELETE_MUTATION

    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    variant_list = [product.variants.first() for product in product_list][:2]
    for variant in variant_list:
        add_variant_to_checkout(checkout_info, variant, 1)

    lines_count = checkout.lines.count()
    lines, _ = fetch_checkout_lines(checkout)
    old_quantity = calculate_checkout_quantity(lines)

    assert ProductVariantChannelListing.objects.filter(
        variant_id__in=[variant.id for variant in variant_list]
    ).exists()

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductVariant", variant.id)
            for variant in variant_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()

    assert content["data"]["productVariantBulkDelete"]["count"] == 2
    assert not ProductVariant.objects.filter(
        id__in=[variant.id for variant in variant_list]
    ).exists()
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)

    assert checkout.lines.count() == lines_count - 2
    assert old_quantity == calculate_checkout_quantity(lines) + 2


@patch("saleor.product.signals.delete_from_storage_task")
@patch("saleor.plugins.manager.PluginsManager.product_variant_deleted")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_variants_with_images(
    mocked_recalculate_orders_task,
    product_variant_deleted_webhook_mock,
    delete_from_storage_task_mock,
    staff_api_client,
    product_variant_list,
    image_list,
    permission_manage_products,
    media_root,
):
    query = PRODUCT_VARIANT_BULK_DELETE_MUTATION

    assert ProductVariantChannelListing.objects.filter(
        variant_id__in=[variant.id for variant in product_variant_list]
    ).exists()

    media1 = ProductMedia.objects.create(
        product=product_variant_list[0].product, image=image_list[0]
    )
    media2 = ProductMedia.objects.create(
        product=product_variant_list[1].product, image=image_list[1]
    )

    VariantMedia.objects.create(variant=product_variant_list[0], media=media1)
    VariantMedia.objects.create(variant=product_variant_list[1], media=media2)

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductVariant", variant.id)
            for variant in product_variant_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()

    assert content["data"]["productVariantBulkDelete"]["count"] == 4
    assert not ProductVariant.objects.filter(
        id__in=[variant.id for variant in product_variant_list]
    ).exists()
    assert (
        product_variant_deleted_webhook_mock.call_count
        == content["data"]["productVariantBulkDelete"]["count"]
    )
    mocked_recalculate_orders_task.assert_not_called()
    delete_from_storage_task_mock.assert_not_called()


def test_product_delete_removes_reference_to_product(
    staff_api_client,
    product_type_product_reference_attribute,
    product_list,
    product_type,
    permission_manage_products,
):
    # given
    query = DELETE_PRODUCTS_MUTATION

    product = product_list[0]
    product_ref = product_list[1]

    product_type.product_attributes.add(product_type_product_reference_attribute)
    attr_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_ref.name,
        slug=f"{product.pk}_{product_ref.pk}",
        reference_product=product_ref,
    )
    associate_attribute_values_to_instance(
        product, product_type_product_reference_attribute, attr_value
    )

    reference_id = graphene.Node.to_global_id("Product", product_ref.pk)

    variables = {"ids": [reference_id]}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productBulkDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(product_ref._meta.model.DoesNotExist):
        product_ref.refresh_from_db()

    assert not data["errors"]


def test_product_delete_removes_reference_to_product_variant(
    staff_api_client,
    variant,
    product_type_product_reference_attribute,
    permission_manage_products,
    product_list,
):
    query = DELETE_PRODUCTS_MUTATION
    product_type = variant.product.product_type
    product_type.variant_attributes.set([product_type_product_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_list[0].name,
        slug=f"{variant.pk}_{product_list[0].pk}",
        reference_product=product_list[0],
    )

    associate_attribute_values_to_instance(
        variant,
        product_type_product_reference_attribute,
        attr_value,
    )
    reference_id = graphene.Node.to_global_id("Product", product_list[0].pk)

    variables = {"ids": [reference_id]}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productBulkDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(product_list[0]._meta.model.DoesNotExist):
        product_list[0].refresh_from_db()

    assert not data["errors"]


def test_product_delete_removes_reference_to_page(
    staff_api_client,
    permission_manage_products,
    page,
    page_type_product_reference_attribute,
    product,
):
    query = DELETE_PRODUCTS_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_type_product_reference_attribute)

    attr_value = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=page.title,
        slug=f"{page.pk}_{product.pk}",
        reference_product=product,
    )
    associate_attribute_values_to_instance(
        page, page_type_product_reference_attribute, attr_value
    )

    reference_id = graphene.Node.to_global_id("Product", product.pk)

    variables = {"ids": [reference_id]}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productBulkDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()

    assert not data["errors"]


@patch("saleor.plugins.manager.PluginsManager.product_variant_deleted")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_variants_with_file_attribute(
    mocked_recalculate_orders_task,
    product_variant_deleted_webhook_mock,
    staff_api_client,
    product_variant_list,
    permission_manage_products,
    file_attribute,
):
    query = PRODUCT_VARIANT_BULK_DELETE_MUTATION

    assert ProductVariantChannelListing.objects.filter(
        variant_id__in=[variant.id for variant in product_variant_list]
    ).exists()

    values = [value for value in file_attribute.values.all()]
    for i, variant in enumerate(product_variant_list[: len(values)]):
        product_type = variant.product.product_type
        product_type.variant_attributes.add(file_attribute)
        existing_value = values[i]
        associate_attribute_values_to_instance(variant, file_attribute, existing_value)

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductVariant", variant.id)
            for variant in product_variant_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()

    assert content["data"]["productVariantBulkDelete"]["count"] == 4
    assert not ProductVariant.objects.filter(
        id__in=[variant.id for variant in product_variant_list]
    ).exists()
    assert (
        product_variant_deleted_webhook_mock.call_count
        == content["data"]["productVariantBulkDelete"]["count"]
    )
    mocked_recalculate_orders_task.assert_not_called()
    for value in values:
        with pytest.raises(value._meta.model.DoesNotExist):
            value.refresh_from_db()


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_variants_in_draft_orders(
    mocked_recalculate_orders_task,
    staff_api_client,
    product_variant_list,
    permission_manage_products,
    order_line,
    order_list,
    channel_USD,
):
    # given
    query = PRODUCT_VARIANT_BULK_DELETE_MUTATION
    variants = product_variant_list

    draft_order = order_line.order
    draft_order.status = OrderStatus.DRAFT
    draft_order.save(update_fields=["status"])

    second_variant_in_draft = variants[1]
    second_product = second_variant_in_draft.product
    second_variant_channel_listing = second_variant_in_draft.channel_listings.get(
        channel=channel_USD
    )
    net = second_variant_in_draft.get_price(
        second_product, [], channel_USD, second_variant_channel_listing, None
    )
    gross = Money(amount=net.amount, currency=net.currency)
    unit_price = TaxedMoney(net=net, gross=gross)
    quantity = 3
    total_price = unit_price * quantity
    second_draft_order = OrderLine.objects.create(
        variant=second_variant_in_draft,
        order=draft_order,
        product_name=str(second_product),
        variant_name=str(second_variant_in_draft),
        product_sku=second_variant_in_draft.sku,
        product_variant_id=second_variant_in_draft.get_global_id(),
        is_shipping_required=second_variant_in_draft.is_shipping_required(),
        is_gift_card=second_variant_in_draft.is_gift_card(),
        unit_price=TaxedMoney(net=net, gross=gross),
        total_price=total_price,
        quantity=quantity,
    )

    variant = variants[0]
    product = variant.product
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    net = variant.get_price(product, [], channel_USD, variant_channel_listing, None)
    gross = Money(amount=net.amount, currency=net.currency)
    unit_price = TaxedMoney(net=net, gross=gross)
    quantity = 3
    total_price = unit_price * quantity
    order_not_draft = order_list[-1]
    order_line_not_in_draft = OrderLine.objects.create(
        variant=variant,
        order=order_not_draft,
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        unit_price=TaxedMoney(net=net, gross=gross),
        total_price=total_price,
        quantity=quantity,
    )
    order_line_not_in_draft_pk = order_line_not_in_draft.pk

    variant_count = ProductVariant.objects.count()

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductVariant", variant.id)
            for variant in ProductVariant.objects.all()
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["productVariantBulkDelete"]["count"] == variant_count
    assert not ProductVariant.objects.filter(
        id__in=[variant.id for variant in product_variant_list]
    ).exists()

    with pytest.raises(order_line._meta.model.DoesNotExist):
        order_line.refresh_from_db()

    with pytest.raises(second_draft_order._meta.model.DoesNotExist):
        second_draft_order.refresh_from_db()

    assert OrderLine.objects.filter(pk=order_line_not_in_draft_pk).exists()
    mocked_recalculate_orders_task.assert_called_once_with([draft_order.id])

    event = OrderEvent.objects.filter(
        type=OrderEvents.ORDER_LINE_VARIANT_DELETED
    ).last()
    assert event
    assert event.order == draft_order
    assert event.user == staff_api_client.user
    expected_params = [
        {
            "item": str(line),
            "line_pk": line.pk,
            "quantity": line.quantity,
        }
        for line in draft_order.lines.all()
    ]
    for param in expected_params:
        assert param in event.parameters


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_variants_delete_default_variant(
    mocked_recalculate_orders_task,
    staff_api_client,
    product,
    permission_manage_products,
):
    # given
    query = PRODUCT_VARIANT_BULK_DELETE_MUTATION

    new_default_variant = product.variants.first()

    variants = ProductVariant.objects.bulk_create(
        [
            ProductVariant(product=product, sku="1"),
            ProductVariant(product=product, sku="2"),
            ProductVariant(product=product, sku="3"),
        ]
    )

    default_variant = variants[0]

    product = default_variant.product
    product.default_variant = default_variant
    product.save(update_fields=["default_variant"])

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductVariant", variant.id)
            for variant in variants
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["productVariantBulkDelete"]["count"] == 3
    assert not ProductVariant.objects.filter(
        id__in=[variant.id for variant in variants]
    ).exists()

    product.refresh_from_db()
    assert product.default_variant.pk == new_default_variant.pk
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_variants_delete_all_product_variants(
    mocked_recalculate_orders_task,
    staff_api_client,
    product,
    permission_manage_products,
):
    # given
    query = PRODUCT_VARIANT_BULK_DELETE_MUTATION

    new_default_variant = product.variants.first()

    variants = ProductVariant.objects.bulk_create(
        [
            ProductVariant(product=product, sku="1"),
            ProductVariant(product=product, sku="2"),
        ]
    )

    default_variant = variants[0]

    product = default_variant.product
    product.default_variant = default_variant
    product.save(update_fields=["default_variant"])

    ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id) for variant in variants
    ]
    ids.append(graphene.Node.to_global_id("ProductVariant", new_default_variant.id))

    variables = {"ids": ids}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["productVariantBulkDelete"]["count"] == 3
    assert not ProductVariant.objects.filter(
        id__in=[variant.id for variant in variants]
    ).exists()

    product.refresh_from_db()
    assert product.default_variant is None
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_variants_from_different_products(
    mocked_recalculate_orders_task,
    staff_api_client,
    product,
    product_with_two_variants,
    permission_manage_products,
):
    # given
    query = PRODUCT_VARIANT_BULK_DELETE_MUTATION

    product_1 = product
    product_2 = product_with_two_variants

    product_1_default_variant = product_1.variants.first()
    product_2_default_variant = product_2.variants.first()

    product_1.default_variant = product_1_default_variant
    product_2.default_variant = product_2_default_variant

    Product.objects.bulk_update([product_1, product_2], ["default_variant"])

    product_2_second_variant = product_2.variants.last()

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductVariant", product_1_default_variant.id),
            graphene.Node.to_global_id("ProductVariant", product_2_default_variant.id),
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["productVariantBulkDelete"]["count"] == 2
    assert not ProductVariant.objects.filter(
        id__in=[product_1_default_variant.id, product_2_default_variant.id]
    ).exists()

    product_1.refresh_from_db()
    product_2.refresh_from_db()

    assert product_1.default_variant is None
    assert product_2.default_variant.pk == product_2_second_variant.pk
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_variants_delete_product_channel_listing_without_available_channel(
    mocked_recalculate_orders_task,
    staff_api_client,
    product,
    product_with_two_variants,
    permission_manage_products,
):
    """Ensure that when the last available variant for channel is removed,
    the corresponging product channel listings will be removed too, and when
    any available variant for channel exist the product channel listing will
    be not removed."""
    # given
    query = PRODUCT_VARIANT_BULK_DELETE_MUTATION

    product_1 = product
    product_2 = product_with_two_variants

    product_1_default_variant = product_1.variants.first()
    product_2_default_variant = product_2.variants.first()

    product_1.default_variant = product_1_default_variant
    product_2.default_variant = product_2_default_variant

    Product.objects.bulk_update([product_1, product_2], ["default_variant"])

    product_2_second_variant = product_2.variants.last()

    assert product_1.channel_listings.count() > 0
    product_2_channel_listings_count = product_2.channel_listings.count()

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductVariant", product_1_default_variant.id),
            graphene.Node.to_global_id("ProductVariant", product_2_default_variant.id),
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["productVariantBulkDelete"]["count"] == 2
    assert not ProductVariant.objects.filter(
        id__in=[product_1_default_variant.id, product_2_default_variant.id]
    ).exists()

    product_1.refresh_from_db()
    product_2.refresh_from_db()

    assert product_1.default_variant is None
    assert product_2.default_variant.pk == product_2_second_variant.pk
    assert product_1.channel_listings.count() == 0
    assert product_2.channel_listings.count() == product_2_channel_listings_count
    mocked_recalculate_orders_task.assert_not_called()
