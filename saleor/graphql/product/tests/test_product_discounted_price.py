from unittest.mock import patch

from freezegun import freeze_time
from graphql_relay import to_global_id

from ....discount.models import Promotion, PromotionRule
from ....discount.utils.promotion import (
    get_active_catalogue_promotion_rules,
    get_current_products_for_rules,
)
from ....product.models import ProductChannelListing
from ...discount.enums import DiscountValueTypeEnum
from ...tests.utils import get_graphql_content


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_product_variant_delete_updates_discounted_price(
    mocked_recalculate_orders_task,
    staff_api_client,
    product,
    permission_manage_products,
):
    # given
    query = """
        mutation ProductVariantDelete($id: ID!) {
            productVariantDelete(id: $id) {
                productVariant {
                    id
                }
                errors {
                    field
                    message
                }
              }
            }
    """
    variant = product.variants.first()
    variant_id = to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantDelete"]
    assert data["errors"] == []
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty
    mocked_recalculate_orders_task.assert_not_called()


def test_category_delete_updates_discounted_price(
    staff_api_client,
    categories_tree_with_published_products,
    permission_manage_products,
):
    # given
    parent = categories_tree_with_published_products
    product_list = [parent.children.first().products.first(), parent.products.first()]

    query = """
        mutation CategoryDelete($id: ID!) {
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
    variables = {"id": to_global_id("Category", parent.pk)}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    assert response.status_code == 200

    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["errors"] == []

    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty

    for product in product_list:
        product.refresh_from_db()
        assert not product.category


def test_collection_add_products_updates_rule_variants_dirty(
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    # given
    assert collection.products.count() == 0
    query = """
        mutation CollectionAddProducts($id: ID!, $products: [ID!]!) {
            collectionAddProducts(collectionId: $id, products: $products) {
                collection {
                    products {
                        totalCount
                    }
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    collection_id = to_global_id("Collection", collection.id)
    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    variables = {"id": collection_id, "products": product_ids}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionAddProducts"]
    assert data["errors"] == []
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty


def test_collection_remove_products_updates_rule_variants_dirty(
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    # given
    assert collection.products.count() == 0
    query = """
        mutation CollectionRemoveProducts($id: ID!, $products: [ID!]!) {
            collectionRemoveProducts(collectionId: $id, products: $products) {
                collection {
                    products {
                        totalCount
                    }
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    collection_id = to_global_id("Collection", collection.id)
    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    variables = {"id": collection_id, "products": product_ids}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionRemoveProducts"]
    assert data["errors"] == []
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty


@freeze_time("2010-05-31 12:00:01")
def test_sale_create_updates_products_discounted_prices(
    staff_api_client,
    permission_manage_discounts,
):
    # given
    query = """
    mutation SaleCreate(
            $name: String,
            $type: DiscountValueTypeEnum,
            $products: [ID!]
    ) {
        saleCreate(input: {
                name: $name,
                type: $type,
                products: $products
        }) {
            sale {
                id
            }
            errors {
                field
                message
            }
        }
    }
    """
    variables = {
        "name": "Half price product",
        "type": DiscountValueTypeEnum.PERCENTAGE.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert content["data"]["saleCreate"]["errors"] == []

    sale = Promotion.objects.filter(name="Half price product").get()
    for rule in sale.rules.all():
        assert rule.variants_dirty is True


def test_sale_update_updates_products_discounted_prices(
    staff_api_client,
    promotion_converted_from_sale,
    product,
    permission_manage_discounts,
):
    # given
    query = """
    mutation SaleUpdate($id: ID!, $type: DiscountValueTypeEnum) {
        saleUpdate(id: $id, input: {type: $type}) {
            sale {
                id
            }
            errors {
                field
                message
            }
        }
    }
    """
    promotion = promotion_converted_from_sale

    variables = {
        "id": to_global_id("Sale", promotion.old_sale_id),
        "type": DiscountValueTypeEnum.PERCENTAGE.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    assert response.status_code == 200
    content = get_graphql_content(response)
    assert content["data"]["saleUpdate"]["errors"] == []
    rules = promotion.rules.all()
    PromotionRuleChannel = PromotionRule.channels.through
    channel_ids = set(
        PromotionRuleChannel.objects.filter(
            promotionrule__in=promotion.rules.all()
        ).values_list("channel_id", flat=True)
    )
    assert not ProductChannelListing.objects.filter(
        product__in=get_current_products_for_rules(rules),
        channel__in=channel_ids,
        discounted_price_dirty=False,
    )


def test_sale_delete_updates_products_discounted_prices(
    staff_api_client,
    promotion_converted_from_sale,
    product,
    permission_manage_discounts,
):
    # given
    query = """
    mutation SaleDelete($id: ID!) {
        saleDelete(id: $id) {
            sale {
                id
            }
            errors {
                field
                message
            }
        }
    }
    """
    promotion = promotion_converted_from_sale
    variables = {"id": to_global_id("Sale", promotion.old_sale_id)}
    rules = promotion.rules.all()
    PromotionRuleChannel = PromotionRule.channels.through
    channel_ids = set(
        PromotionRuleChannel.objects.filter(
            promotionrule__in=promotion.rules.all()
        ).values_list("channel_id", flat=True)
    )
    products = list(get_current_products_for_rules(rules))

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert content["data"]["saleDelete"]["errors"] == []

    assert not ProductChannelListing.objects.filter(
        product__in=products, channel__in=channel_ids, discounted_price_dirty=False
    )


def test_sale_add_catalogues_updates_products_discounted_prices(
    staff_api_client,
    promotion_converted_from_sale_with_empty_predicate,
    product_list,
    permission_manage_discounts,
):
    # given
    query = """
        mutation SaleCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            saleCataloguesAdd(id: $id, input: $input) {
                sale {
                    name
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    promotion = promotion_converted_from_sale_with_empty_predicate
    sale_id = to_global_id("Sale", promotion.old_sale_id)
    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    predicate = {"OR": [{"productPredicate": {"ids": [product_ids[0]]}}]}
    rule = promotion.rules.first()
    rule.catalogue_predicate = predicate
    rule.save(update_fields=["catalogue_predicate"])

    variables = {
        "id": sale_id,
        "input": {
            "products": product_ids[1:],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesAdd"]["errors"]


def test_sale_remove_catalogues_updates_products_discounted_prices(
    staff_api_client,
    promotion_converted_from_sale_with_empty_predicate,
    product_list,
    permission_manage_discounts,
):
    # given
    promotion = promotion_converted_from_sale_with_empty_predicate
    sale_id = to_global_id("Sale", promotion.old_sale_id)
    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    predicate = {"OR": [{"productPredicate": {"ids": product_ids}}]}
    rule = promotion.rules.first()
    rule.catalogue_predicate = predicate
    rule.save(update_fields=["catalogue_predicate"])
    product_id = to_global_id("Product", product_list[-1].pk)

    query = """
        mutation SaleCataloguesRemove($id: ID!, $input: CatalogueInput!) {
            saleCataloguesRemove(id: $id, input: $input) {
                sale {
                    name
                }
                errors {
                    field
                    message
                }
            }
        }
    """

    variables = {
        "id": sale_id,
        "input": {
            "products": [product_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesRemove"]["errors"]

    for listing in ProductChannelListing.objects.filter(
        product=product_list[-1],
        channel__in=rule.channels.all(),
    ):
        assert listing.discounted_price_dirty
