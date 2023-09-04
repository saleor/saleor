import logging
from unittest.mock import patch

from ....discount.tests.sale_converter import convert_sales_to_promotions
from ...tasks import (
    update_product_discounted_price_task,
    update_products_discounted_prices_of_sale_task,
)


@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
def test_update_products_discounted_prices_of_sale_task(
    update_discounted_prices_for_promotion_mock,
    new_sale,
    product_list,
    product,
    category,
    collection,
):
    # given
    new_sale.products.add(product)
    category.products.add(product_list[0])
    new_sale.categories.add(category)
    collection.products.add(product_list[1])
    new_sale.variants.add(product_list[2].variants.first())
    convert_sales_to_promotions()

    # when
    update_products_discounted_prices_of_sale_task(new_sale.id)

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
