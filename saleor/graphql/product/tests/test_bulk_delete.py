from unittest.mock import patch

import graphene
import pytest
from django.utils import timezone
from prices import Money, TaxedMoney

from ....order import OrderStatus
from ....order.models import OrderLine
from ....product.models import (
    Category,
    Collection,
    Product,
    ProductChannelListing,
    ProductImage,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
)
from ...tests.utils import get_graphql_content


@pytest.fixture
def category_list():
    category_1 = Category.objects.create(name="Category 1", slug="category-1")
    category_2 = Category.objects.create(name="Category 2", slug="category-2")
    category_3 = Category.objects.create(name="Category 3", slug="category-3")
    return category_1, category_2, category_3


@pytest.fixture
def product_type_list():
    product_type_1 = ProductType.objects.create(name="Type 1", slug="type-1")
    product_type_2 = ProductType.objects.create(name="Type 2", slug="type-2")
    product_type_3 = ProductType.objects.create(name="Type 3", slug="type-3")
    return product_type_1, product_type_2, product_type_3


MUTATION_CATEGORY_BULK_DELETE = """
    mutation categoryBulkDelete($ids: [ID]!) {
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
                publication_date=timezone.now(),
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
        assert not product_channel_listing.publication_date
    assert product_channel_listings.count() == 3


def test_delete_collections(
    staff_api_client, collection_list, permission_manage_products
):
    query = """
    mutation collectionBulkDelete($ids: [ID]!) {
        collectionBulkDelete(ids: $ids) {
            count
        }
    }
    """

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


DELETE_PRODUCTS_MUTATION = """
mutation productBulkDelete($ids: [ID]!) {
    productBulkDelete(ids: $ids) {
        count
    }
}
"""


def test_delete_products(
    staff_api_client, product_list, permission_manage_products, order_list, channel_USD
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
            is_shipping_required=variant.is_shipping_required(),
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
            is_shipping_required=variant.is_shipping_required(),
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


def test_delete_products_variants_in_draft_order(
    staff_api_client, product_list, permission_manage_products
):
    query = DELETE_PRODUCTS_MUTATION

    assert ProductChannelListing.objects.filter(
        product_id__in=[product.id for product in product_list]
    ).exists()

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
    assert not Product.objects.filter(
        id__in=[product.id for product in product_list]
    ).exists()
    assert not ProductChannelListing.objects.filter(
        product_id__in=[product.id for product in product_list]
    ).exists()


def test_delete_product_images(
    staff_api_client, product_with_images, permission_manage_products
):
    images = product_with_images.images.all()

    query = """
    mutation productImageBulkDelete($ids: [ID]!) {
        productImageBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductImage", image.id) for image in images
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["productImageBulkDelete"]["count"] == 2
    assert not ProductImage.objects.filter(
        id__in=[image.id for image in images]
    ).exists()


def test_delete_product_types(
    staff_api_client, product_type_list, permission_manage_product_types_and_attributes
):
    query = """
    mutation productTypeBulkDelete($ids: [ID]!) {
        productTypeBulkDelete(ids: $ids) {
            count
        }
    }
    """

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


PRODUCT_VARIANT_BULK_DELETE_MUTATION = """
mutation productVariantBulkDelete($ids: [ID]!) {
    productVariantBulkDelete(ids: $ids) {
        count
    }
}
"""


def test_delete_product_variants(
    staff_api_client, product_variant_list, permission_manage_products
):
    query = PRODUCT_VARIANT_BULK_DELETE_MUTATION

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

    assert content["data"]["productVariantBulkDelete"]["count"] == 3
    assert not ProductVariant.objects.filter(
        id__in=[variant.id for variant in product_variant_list]
    ).exists()


def test_delete_product_variants_in_draft_orders(
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
        is_shipping_required=second_variant_in_draft.is_shipping_required(),
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
        is_shipping_required=variant.is_shipping_required(),
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


def test_delete_product_variants_delete_default_variant(
    staff_api_client, product, permission_manage_products
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


def test_delete_product_variants_delete_all_product_variants(
    staff_api_client, product, permission_manage_products
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


def test_delete_product_variants_from_different_products(
    staff_api_client, product, product_with_two_variants, permission_manage_products
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
