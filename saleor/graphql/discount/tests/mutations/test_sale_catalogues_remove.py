from unittest.mock import patch

import graphene

from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Promotion
from .....discount.sale_converter import convert_sales_to_promotions
from .....discount.utils import fetch_catalogue_info
from ....tests.utils import get_graphql_content
from ...mutations.utils import convert_catalogue_info_to_global_ids
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


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_remove_catalogues(
    updated_webhook_mock,
    update_products_discounted_prices_for_promotion_task_mock,
    staff_api_client,
    sale,
    category,
    product,
    collection,
    variant,
    product_list,
    permission_manage_discounts,
):
    # given
    sale.products.add(product_list[0])

    assert collection in sale.collections.all()
    assert category in sale.categories.all()
    assert product in sale.products.all()
    assert variant in sale.variants.all()

    query = SALE_CATALOGUES_REMOVE_MUTATION
    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    convert_sales_to_promotions()

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
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
    assert content["data"]["saleCataloguesRemove"]["sale"]["name"] == sale.name
    promotion = Promotion.objects.get(old_sale_id=sale.id)
    predicate = promotion.rules.first().catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    assert collection_id not in current_catalogue["collections"]
    assert category_id not in current_catalogue["categories"]
    assert product_id not in current_catalogue["products"]
    assert variant_id not in current_catalogue["variants"]

    assert (
        graphene.Node.to_global_id("Product", product_list[0].id)
        in current_catalogue["products"]
    )

    updated_webhook_mock.assert_called_once_with(
        promotion, previous_catalogue, current_catalogue
    )
    update_products_discounted_prices_for_promotion_task_mock.assert_called_once()


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_remove_empty_catalogues(
    updated_webhook_mock,
    update_products_discounted_prices_for_promotion_task_mock,
    staff_api_client,
    sale,
    category,
    product,
    collection,
    variant,
    permission_manage_discounts,
):
    # given
    assert collection in sale.collections.all()
    assert category in sale.categories.all()
    assert product in sale.products.all()
    assert variant in sale.variants.all()

    query = SALE_CATALOGUES_REMOVE_MUTATION
    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )

    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    convert_sales_to_promotions()

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
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
    assert content["data"]["saleCataloguesRemove"]["sale"]["name"] == sale.name
    promotion = Promotion.objects.get(old_sale_id=sale.id)
    predicate = promotion.rules.first().catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)
    assert current_catalogue == previous_catalogue

    assert collection_id in current_catalogue["collections"]
    assert category_id in current_catalogue["categories"]
    assert product_id in current_catalogue["products"]
    assert variant_id in current_catalogue["variants"]

    updated_webhook_mock.assert_not_called()
    update_products_discounted_prices_for_promotion_task_mock.assert_not_called()


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_remove_empty_catalogues_from_sale_with_empty_catalogues(
    updated_webhook_mock,
    update_products_discounted_prices_for_promotion_task_mock,
    staff_api_client,
    new_sale,
    permission_manage_discounts,
):
    # given
    sale = new_sale
    query = SALE_CATALOGUES_REMOVE_MUTATION
    convert_sales_to_promotions()

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
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
    assert content["data"]["saleCataloguesRemove"]["sale"]["name"] == sale.name
    promotion = Promotion.objects.get(old_sale_id=sale.id)
    predicate = promotion.rules.first().catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    assert not current_catalogue["collections"]
    assert not current_catalogue["categories"]
    assert not current_catalogue["products"]
    assert not current_catalogue["variants"]

    updated_webhook_mock.assert_not_called()
    update_products_discounted_prices_for_promotion_task_mock.assert_not_called()


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_remove_catalogues_no_product_changes(
    updated_webhook_mock,
    update_products_discounted_prices_for_promotion_task_mock,
    staff_api_client,
    sale,
    variant,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_REMOVE_MUTATION
    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    convert_sales_to_promotions()

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
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
    assert content["data"]["saleCataloguesRemove"]["sale"]["name"] == sale.name
    promotion = Promotion.objects.get(old_sale_id=sale.id)
    predicate = promotion.rules.first().catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    assert variant_id not in current_catalogue["variants"]

    updated_webhook_mock.assert_called_once_with(
        promotion, previous_catalogue, current_catalogue
    )
    update_products_discounted_prices_for_promotion_task_mock.assert_not_called()


def test_sale_remove_catalogues_with_promotion_id(
    staff_api_client,
    sale,
    product,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_REMOVE_MUTATION
    product_id = graphene.Node.to_global_id("Product", product.id)
    convert_sales_to_promotions()

    promotion = Promotion.objects.get(old_sale_id=sale.id)

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
