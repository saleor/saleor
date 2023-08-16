from unittest.mock import patch

import graphene

from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Promotion
from .....discount.sale_converter import convert_sales_to_promotions
from .....discount.utils import fetch_catalogue_info
from ....tests.utils import get_graphql_content
from ...mutations.utils import convert_catalogue_info_to_global_ids
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


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_add_catalogues(
    updated_webhook_mock,
    update_products_discounted_prices_for_promotion_task_mock,
    staff_api_client,
    new_sale,
    category,
    product,
    collection,
    product_variant_list,
    permission_manage_discounts,
):
    # given
    sale = new_sale
    query = SALE_CATALOGUES_ADD_MUTATION
    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
        for variant in product_variant_list
    ]
    convert_sales_to_promotions()

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
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
    assert content["data"]["saleCataloguesAdd"]["sale"]["name"] == sale.name
    promotion = Promotion.objects.get(old_sale_id=sale.id)
    predicate = promotion.rules.first().catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    assert collection_id in current_catalogue["collections"]
    assert category_id in current_catalogue["categories"]
    assert product_id in current_catalogue["products"]
    assert all([variant in current_catalogue["variants"] for variant in variant_ids])

    updated_webhook_mock.assert_called_once_with(
        promotion, previous_catalogue, current_catalogue
    )
    update_products_discounted_prices_for_promotion_task_mock.assert_called_once()


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_add_catalogues_no_changes_in_catalogue(
    updated_webhook_mock,
    update_products_discounted_prices_for_promotion_task_mock,
    staff_api_client,
    sale,
    collection,
    category,
    product,
    variant,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION
    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    product_id = graphene.Node.to_global_id("Product", product.id)
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
    assert not content["data"]["saleCataloguesAdd"]["errors"]
    promotion = Promotion.objects.get(old_sale_id=sale.id)
    predicate = promotion.rules.first().catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    assert collection_id in current_catalogue["collections"]
    assert category_id in current_catalogue["categories"]
    assert product_id in current_catalogue["products"]
    assert variant_id in current_catalogue["variants"]
    assert current_catalogue == previous_catalogue

    updated_webhook_mock.assert_not_called()
    update_products_discounted_prices_for_promotion_task_mock.assert_not_called()


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_add_empty_catalogues(
    updated_webhook_mock,
    update_products_discounted_prices_for_promotion_task_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION

    product_id = graphene.Node.to_global_id("Product", sale.products.first().id)
    collection_id = graphene.Node.to_global_id(
        "Collection", sale.collections.first().id
    )
    category_id = graphene.Node.to_global_id("Category", sale.categories.first().id)
    variant_id = graphene.Node.to_global_id("ProductVariant", sale.variants.first().id)

    convert_sales_to_promotions()
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {"products": [], "collections": [], "categories": [], "variants": []},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesAdd"]["errors"]
    promotion = Promotion.objects.get(old_sale_id=sale.id)
    predicate = promotion.rules.first().catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

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
def test_sale_add_empty_catalogues_to_sale_with_empty_catalogues(
    updated_webhook_mock,
    update_products_discounted_prices_for_promotion_task_mock,
    staff_api_client,
    new_sale,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION
    convert_sales_to_promotions()
    variables = {
        "id": graphene.Node.to_global_id("Sale", new_sale.id),
        "input": {"products": [], "collections": [], "categories": [], "variants": []},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesAdd"]["errors"]
    promotion = Promotion.objects.get(old_sale_id=new_sale.id)
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
def test_sale_add_catalogues_no_product_ids_change(
    updated_webhook_mock,
    update_products_discounted_prices_for_promotion_task_mock,
    staff_api_client,
    sale,
    product_variant_list,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION
    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
        for variant in product_variant_list
    ]

    product = sale.products.first()
    for variant in product_variant_list:
        assert variant.product == product

    convert_sales_to_promotions()

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
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
    promotion = Promotion.objects.get(old_sale_id=sale.id)
    predicate = promotion.rules.first().catalogue_predicate
    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    updated_webhook_mock.assert_called_once_with(
        promotion, previous_catalogue, current_catalogue
    )
    update_products_discounted_prices_for_promotion_task_mock.assert_not_called()


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
def test_sale_add_catalogues_with_product_without_variants(
    update_products_discounted_prices_for_promotion_task_mock,
    staff_api_client,
    sale,
    category,
    product,
    collection,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION
    product.variants.all().delete()
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    convert_sales_to_promotions()

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
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
    update_products_discounted_prices_for_promotion_task_mock.assert_not_called()


def test_sale_add_catalogues_with_promotion_id(
    staff_api_client,
    sale,
    product,
    permission_manage_discounts,
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION
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
    error = content["data"]["saleCataloguesAdd"]["errors"][0]

    assert error["code"] == DiscountErrorCode.INVALID.name
    assert error["message"] == (
        "Provided ID refers to Promotion model. "
        "Please use 'promotionRuleCreate' mutation instead."
    )
