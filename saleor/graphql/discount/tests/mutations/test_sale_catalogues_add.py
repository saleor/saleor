from unittest.mock import patch

import graphene

from .....discount.error_codes import DiscountErrorCode
from .....product.models import ProductChannelListing
from ....tests.utils import get_graphql_content
from ...utils import convert_migrated_sale_predicate_to_catalogue_info

SALE_CATALOGUES_ADD_MUTATION = """
    mutation saleCataloguesAdd($id: ID!, $input: CatalogueInput!) {
        saleCataloguesAdd(id: $id, input: $input) {
            sale {
                name
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_add_catalogues(
    updated_webhook_mock,
    staff_api_client,
    promotion_converted_from_sale_with_empty_predicate,
    category,
    product,
    collection,
    product_variant_list,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION
    promotion = promotion_converted_from_sale_with_empty_predicate
    previous_catalogue = convert_migrated_sale_predicate_to_catalogue_info({})
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
        for variant in product_variant_list
    ]

    variables = {
        "id": graphene.Node.to_global_id("Sale", promotion.old_sale_id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
            "variants": variant_ids,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesAdd"]["errors"]
    assert content["data"]["saleCataloguesAdd"]["sale"]["name"] == promotion.name
    promotion.refresh_from_db()
    rule = promotion.rules.first()
    predicate = rule.catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    assert collection_id in current_catalogue["collections"]
    assert category_id in current_catalogue["categories"]
    assert product_id in current_catalogue["products"]
    assert all([variant in current_catalogue["variants"] for variant in variant_ids])

    updated_webhook_mock.assert_called_once_with(
        promotion, previous_catalogue, current_catalogue
    )
    for listing in ProductChannelListing.objects.filter(
        channel__in=rule.channels.all(), product=product
    ):
        assert listing.discounted_price_dirty is True


@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_add_catalogues_no_changes_in_catalogue(
    updated_webhook_mock,
    staff_api_client,
    promotion_converted_from_sale,
    catalogue_predicate,
    collection,
    category,
    product,
    variant,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION
    promotion = promotion_converted_from_sale
    previous_catalogue = convert_migrated_sale_predicate_to_catalogue_info(
        catalogue_predicate
    )
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    product_id = graphene.Node.to_global_id("Product", product.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {
        "id": graphene.Node.to_global_id("Sale", promotion.old_sale_id),
        "input": {
            "collections": [collection_id],
            "categories": [category_id],
            "products": [product_id],
            "variants": [variant_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesAdd"]["errors"]
    promotion.refresh_from_db()
    rule = promotion.rules.first()
    predicate = rule.catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    assert collection_id in current_catalogue["collections"]
    assert category_id in current_catalogue["categories"]
    assert product_id in current_catalogue["products"]
    assert variant_id in current_catalogue["variants"]
    assert current_catalogue == previous_catalogue

    updated_webhook_mock.assert_not_called()
    for listing in ProductChannelListing.objects.filter(
        channel__in=rule.channels.all(), product=product
    ):
        assert listing.discounted_price_dirty is False


@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_add_empty_catalogues(
    updated_webhook_mock,
    staff_api_client,
    promotion_converted_from_sale,
    catalogue_predicate,
    collection,
    category,
    product,
    variant,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION
    promotion = promotion_converted_from_sale
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    product_id = graphene.Node.to_global_id("Product", product.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {
        "id": graphene.Node.to_global_id("Sale", promotion.old_sale_id),
        "input": {"products": [], "collections": [], "categories": [], "variants": []},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesAdd"]["errors"]
    promotion.refresh_from_db()
    rule = promotion.rules.first()
    predicate = rule.catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    assert collection_id in current_catalogue["collections"]
    assert category_id in current_catalogue["categories"]
    assert product_id in current_catalogue["products"]
    assert variant_id in current_catalogue["variants"]

    updated_webhook_mock.assert_not_called()
    for listing in ProductChannelListing.objects.filter(
        channel__in=rule.channels.all(), product=product
    ):
        assert listing.discounted_price_dirty is False


@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_add_empty_catalogues_to_sale_with_empty_catalogues(
    updated_webhook_mock,
    staff_api_client,
    promotion_converted_from_sale_with_empty_predicate,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION
    promotion = promotion_converted_from_sale_with_empty_predicate

    variables = {
        "id": graphene.Node.to_global_id("Sale", promotion.old_sale_id),
        "input": {"products": [], "collections": [], "categories": [], "variants": []},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesAdd"]["errors"]
    promotion.refresh_from_db()
    predicate = promotion.rules.first().catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    assert not current_catalogue["collections"]
    assert not current_catalogue["categories"]
    assert not current_catalogue["products"]
    assert not current_catalogue["variants"]

    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_add_catalogues_no_product_ids_change(
    updated_webhook_mock,
    staff_api_client,
    promotion_converted_from_sale,
    catalogue_predicate,
    product,
    product_variant_list,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION
    promotion = promotion_converted_from_sale
    previous_catalogue = convert_migrated_sale_predicate_to_catalogue_info(
        catalogue_predicate
    )
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
        for variant in product_variant_list
    ]

    for variant in product_variant_list:
        assert variant.product == product

    variables = {
        "id": graphene.Node.to_global_id("Sale", promotion.old_sale_id),
        "input": {
            "variants": variant_ids,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesAdd"]["errors"]
    promotion.refresh_from_db()
    rule = promotion.rules.first()
    predicate = rule.catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    updated_webhook_mock.assert_called_once_with(
        promotion, previous_catalogue, current_catalogue
    )
    for listing in ProductChannelListing.objects.filter(
        channel__in=rule.channels.all(), product=product
    ):
        assert listing.discounted_price_dirty is False


def test_sale_add_catalogues_with_product_without_variants(
    staff_api_client,
    promotion_converted_from_sale,
    catalogue_predicate,
    category,
    product,
    collection,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION
    promotion = promotion_converted_from_sale
    rule = promotion.rules.first()
    product.variants.all().delete()
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)

    variables = {
        "id": graphene.Node.to_global_id("Sale", promotion.old_sale_id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    error = content["data"]["saleCataloguesAdd"]["errors"][0]

    assert error["code"] == DiscountErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT.name
    assert error["message"] == "Cannot manage products without variants."
    for listing in ProductChannelListing.objects.filter(
        channel__in=rule.channels.all(), product=product
    ):
        assert listing.discounted_price_dirty is False


def test_sale_add_catalogues_with_promotion_id(
    staff_api_client,
    promotion_converted_from_sale,
    product,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION
    promotion = promotion_converted_from_sale
    product_id = graphene.Node.to_global_id("Product", product.id)

    variables = {
        "id": graphene.Node.to_global_id("Promotion", promotion.id),
        "input": {
            "products": [product_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    error = content["data"]["saleCataloguesAdd"]["errors"][0]

    assert error["code"] == DiscountErrorCode.INVALID.name
    assert error["message"] == (
        "Provided ID refers to Promotion model. "
        "Please use 'promotionRuleCreate' mutation instead."
    )


def test_sale_add_catalogues_not_found_error(
    staff_api_client,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Sale", "0"),
        "input": {"products": []},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesAdd"]["sale"]
    errors = content["data"]["saleCataloguesAdd"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == DiscountErrorCode.NOT_FOUND.name
