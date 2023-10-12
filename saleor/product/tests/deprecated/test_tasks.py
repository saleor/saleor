import logging
from unittest.mock import patch

import graphene

from ...tasks import (
    update_product_discounted_price_task,
    update_products_discounted_prices_of_sale_task,
)


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
def test_update_products_discounted_prices_of_sale_task(
    update_discounted_prices_for_promotion_mock,
    promotion_converted_from_sale_with_empty_predicate,
    product_list,
    product,
    category,
    collection,
):
    # given
    promotion = promotion_converted_from_sale_with_empty_predicate
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    product_id = graphene.Node.to_global_id("Product", product.id)
    variant_id = graphene.Node.to_global_id(
        "ProductVariant", product_list[2].variants.first().id
    )

    category.products.add(product_list[0])
    collection.products.add(product_list[1])

    predicate = {
        "OR": [
            {"collectionPredicate": {"ids": [collection_id]}},
            {"categoryPredicate": {"ids": [category_id]}},
            {"productPredicate": {"ids": [product_id]}},
            {"variantPredicate": {"ids": [variant_id]}},
        ]
    }
    rule = promotion.rules.first()
    rule.catalogue_predicate = predicate
    rule.save(update_fields=["catalogue_predicate"])

    # when
    update_products_discounted_prices_of_sale_task(promotion.old_sale_id)

    # then
    update_discounted_prices_for_promotion_mock.assert_called_once()
    args, kwargs = update_discounted_prices_for_promotion_mock.call_args

    expected_products = [product] + product_list
    assert len(args[0]) == len(expected_products)
    assert set(args[0]) == {instance.id for instance in expected_products}


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
def test_update_products_discounted_prices_of_sale_task_discount_does_not_exist(
    update_discounted_prices_for_promotion_mock, caplog
):
    # given
    caplog.set_level(logging.WARNING)
    discount_id = -1

    # when
    update_products_discounted_prices_of_sale_task(discount_id)

    # then
    update_discounted_prices_for_promotion_mock.assert_not_called()
    assert f"Cannot find discount with id: {discount_id}" in caplog.text


@patch("saleor.product.tasks.update_discounted_prices_for_promotion")
def test_update_product_discounted_price_task(
    update_discounted_prices_for_promotion_mock, product
):
    # when
    update_product_discounted_price_task(product.id)

    # then
    update_discounted_prices_for_promotion_mock.assert_called_once()
    args, kwargs = update_discounted_prices_for_promotion_mock.call_args
    assert args[0][0].id == product.id


@patch("saleor.product.tasks.update_discounted_prices_for_promotion")
def test_update_product_discounted_price_task_product_does_not_exist(
    update_discounted_prices_for_promotion_mock, caplog
):
    # given
    caplog.set_level(logging.WARNING)
    product_id = -1

    # when
    update_product_discounted_price_task(product_id)

    # then
    update_discounted_prices_for_promotion_mock.assert_not_called()
    assert f"Cannot find product with id: {product_id}" in caplog.text
