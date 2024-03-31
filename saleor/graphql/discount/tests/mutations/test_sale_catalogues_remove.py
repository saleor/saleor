from unittest.mock import patch

import graphene

from .....discount.error_codes import DiscountErrorCode
from .....product.models import ProductChannelListing
from ....tests.utils import get_graphql_content
from ...utils import convert_migrated_sale_predicate_to_catalogue_info

SALE_CATALOGUES_REMOVE_MUTATION = """
    mutation saleCataloguesRemove($id: ID!, $input: CatalogueInput!) {
        saleCataloguesRemove(id: $id, input: $input) {
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
def test_sale_remove_catalogues(
    updated_webhook_mock,
    staff_api_client,
    promotion_converted_from_sale,
    catalogue_predicate,
    category,
    product,
    collection,
    variant,
    product_list,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_REMOVE_MUTATION
    promotion = promotion_converted_from_sale
    predicate = catalogue_predicate
    extra_product = product_list[0]
    extra_product_id = graphene.Node.to_global_id("Product", extra_product.id)
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    predicate["OR"][2]["productPredicate"]["ids"].append(extra_product_id)
    rule = promotion.rules.first()
    rule.catalogue_predicate = predicate
    rule.save(update_fields=["catalogue_predicate"])
    previous_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    assert collection_id in previous_catalogue["collections"]
    assert category_id in previous_catalogue["categories"]
    assert product_id in previous_catalogue["products"]
    assert extra_product_id in previous_catalogue["products"]
    assert variant_id in previous_catalogue["variants"]

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
    assert not content["data"]["saleCataloguesRemove"]["errors"]
    assert content["data"]["saleCataloguesRemove"]["sale"]["name"] == promotion.name
    promotion.refresh_from_db()
    rule = promotion.rules.first()
    predicate = rule.catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    assert collection_id not in current_catalogue["collections"]
    assert category_id not in current_catalogue["categories"]
    assert product_id not in current_catalogue["products"]
    assert variant_id not in current_catalogue["variants"]

    assert extra_product_id in current_catalogue["products"]

    updated_webhook_mock.assert_called_once_with(
        promotion, previous_catalogue, current_catalogue
    )
    for listing in ProductChannelListing.objects.filter(
        channel__in=rule.channels.all(), product=product
    ):
        assert listing.discounted_price_dirty is True


@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_remove_empty_catalogues(
    updated_webhook_mock,
    staff_api_client,
    promotion_converted_from_sale,
    catalogue_predicate,
    category,
    product,
    collection,
    variant,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_REMOVE_MUTATION
    promotion = promotion_converted_from_sale
    previous_catalogue = convert_migrated_sale_predicate_to_catalogue_info(
        catalogue_predicate
    )
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    assert collection_id in previous_catalogue["collections"]
    assert category_id in previous_catalogue["categories"]
    assert product_id in previous_catalogue["products"]
    assert variant_id in previous_catalogue["variants"]

    variables = {
        "id": graphene.Node.to_global_id("Sale", promotion.old_sale_id),
        "input": {
            "collections": [],
            "categories": [],
            "products": [],
            "variants": [],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesRemove"]["errors"]
    assert content["data"]["saleCataloguesRemove"]["sale"]["name"] == promotion.name
    promotion.refresh_from_db()
    rule = promotion.rules.first()
    predicate = rule.catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)
    assert current_catalogue == previous_catalogue

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
def test_sale_remove_empty_catalogues_from_sale_with_empty_catalogues(
    updated_webhook_mock,
    staff_api_client,
    promotion_converted_from_sale_with_empty_predicate,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_REMOVE_MUTATION
    promotion = promotion_converted_from_sale_with_empty_predicate

    variables = {
        "id": graphene.Node.to_global_id("Sale", promotion.old_sale_id),
        "input": {
            "collections": [],
            "categories": [],
            "products": [],
            "variants": [],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesRemove"]["errors"]
    assert content["data"]["saleCataloguesRemove"]["sale"]["name"] == promotion.name
    promotion.refresh_from_db()
    predicate = promotion.rules.first().catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    assert not current_catalogue["collections"]
    assert not current_catalogue["categories"]
    assert not current_catalogue["products"]
    assert not current_catalogue["variants"]

    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_remove_catalogues_no_product_changes(
    updated_webhook_mock,
    staff_api_client,
    promotion_converted_from_sale,
    catalogue_predicate,
    variant,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_REMOVE_MUTATION
    promotion = promotion_converted_from_sale
    previous_catalogue = convert_migrated_sale_predicate_to_catalogue_info(
        catalogue_predicate
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {
        "id": graphene.Node.to_global_id("Sale", promotion.old_sale_id),
        "input": {
            "products": [],
            "variants": [variant_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesRemove"]["errors"]
    assert content["data"]["saleCataloguesRemove"]["sale"]["name"] == promotion.name
    promotion.refresh_from_db()
    rule = promotion.rules.first()
    predicate = rule.catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    assert variant_id not in current_catalogue["variants"]

    updated_webhook_mock.assert_called_once_with(
        promotion, previous_catalogue, current_catalogue
    )
    for listing in ProductChannelListing.objects.filter(
        channel__in=rule.channels.all(), product=variant.product
    ):
        assert listing.discounted_price_dirty is False


def test_sale_remove_catalogues_with_promotion_id(
    staff_api_client,
    promotion_converted_from_sale,
    product,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_REMOVE_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.id)
    promotion = promotion_converted_from_sale

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
    error = content["data"]["saleCataloguesRemove"]["errors"][0]

    assert error["code"] == DiscountErrorCode.INVALID.name
    assert error["message"] == (
        "Provided ID refers to Promotion model. Please use "
        "`promotionRuleUpdate` or `promotionRuleDelete` mutation instead."
    )


def test_sale_remove_catalogues_not_found_error(
    staff_api_client,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_REMOVE_MUTATION
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
    assert not content["data"]["saleCataloguesRemove"]["sale"]
    errors = content["data"]["saleCataloguesRemove"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == DiscountErrorCode.NOT_FOUND.name
