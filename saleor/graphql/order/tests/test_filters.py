from unittest.mock import ANY, patch

import pytest

from ....order.models import Order
from ..filters import (
    _filter_by_customer_full_name,
    _filter_customer_by_email_first_or_last_name,
    filter_customer,
)


@pytest.fixture
def similar_customers_with_orders(order, customer_user, customer_user2, channel_USD):
    customer_user.first_name = "Test"
    customer_user.last_name = "User"
    customer_user.save()
    customer_user2.first_name = "tester"
    customer_user2.last_name = "users"
    customer_user2.save()
    order2 = Order.objects.create(
        billing_address=customer_user2.default_billing_address,
        channel=channel_USD,
        user_email=customer_user2.email,
        user=customer_user2,
    )
    return order, order2, customer_user, customer_user2


@patch(
    "saleor.graphql.order.filters._filter_customer_by_email_first_or_last_name",
    wraps=_filter_customer_by_email_first_or_last_name,
)
@patch(
    "saleor.graphql.order.filters._filter_by_customer_full_name",
    wraps=_filter_by_customer_full_name,
)
def test_filter_customer_by_email(
    mock_filter_by_customer_full_name,
    mock_filter_customer_by_email_first_or_last_name,
    similar_customers_with_orders,
):
    # given
    order, order2, customer_user, customer_user2 = similar_customers_with_orders
    qs = Order.objects.all()
    value = customer_user.email

    # when
    qs = filter_customer(qs, None, value)

    # then
    assert qs.count() == 1
    assert qs.first() == order
    mock_filter_by_customer_full_name.assert_not_called()
    mock_filter_customer_by_email_first_or_last_name.assert_not_called()


@patch(
    "saleor.graphql.order.filters._filter_customer_by_email_first_or_last_name",
    wraps=_filter_customer_by_email_first_or_last_name,
)
@patch(
    "saleor.graphql.order.filters._filter_by_customer_full_name",
    wraps=_filter_by_customer_full_name,
)
def test_filter_customer_by_first_name(
    mock_filter_by_customer_full_name,
    mock_filter_customer_by_email_first_or_last_name,
    similar_customers_with_orders,
):
    # given
    order, order2, customer_user, customer_user2 = similar_customers_with_orders
    qs = Order.objects.all()
    value = customer_user.first_name

    # when
    qs = filter_customer(qs, None, value)

    # then
    assert qs.count() == 2
    assert order in qs
    assert order2 in qs
    mock_filter_by_customer_full_name.assert_called_once_with(ANY, value)
    mock_filter_customer_by_email_first_or_last_name.assert_called_once_with(ANY, value)


@patch(
    "saleor.graphql.order.filters._filter_customer_by_email_first_or_last_name",
    wraps=_filter_customer_by_email_first_or_last_name,
)
@patch(
    "saleor.graphql.order.filters._filter_by_customer_full_name",
    wraps=_filter_by_customer_full_name,
)
def test_filter_customer_by_last_name(
    mock_filter_by_customer_full_name,
    mock_filter_customer_by_email_first_or_last_name,
    similar_customers_with_orders,
):
    # given
    order, order2, customer_user, customer_user2 = similar_customers_with_orders
    qs = Order.objects.all()
    value = customer_user.last_name

    # when
    qs = filter_customer(qs, None, value)

    # then
    assert qs.count() == 2
    assert order in qs
    assert order2 in qs
    mock_filter_by_customer_full_name.assert_called_once_with(ANY, value)
    mock_filter_customer_by_email_first_or_last_name.assert_called_once_with(ANY, value)


@patch(
    "saleor.graphql.order.filters._filter_customer_by_email_first_or_last_name",
    wraps=_filter_customer_by_email_first_or_last_name,
)
@patch(
    "saleor.graphql.order.filters._filter_by_customer_full_name",
    wraps=_filter_by_customer_full_name,
)
def test_filter_customer_by_full_name_first_last_name(
    mock_filter_by_customer_full_name,
    mock_filter_customer_by_email_first_or_last_name,
    similar_customers_with_orders,
):
    # given
    order, order2, customer_user, customer_user2 = similar_customers_with_orders
    qs = Order.objects.all()
    value = f"{customer_user.first_name} {customer_user.last_name}"

    # when
    qs = filter_customer(qs, None, value)

    # then
    assert qs.count() == 1
    assert qs.first() == order
    mock_filter_by_customer_full_name.assert_called_once_with(ANY, value)
    mock_filter_customer_by_email_first_or_last_name.assert_not_called()


@patch(
    "saleor.graphql.order.filters._filter_customer_by_email_first_or_last_name",
    wraps=_filter_customer_by_email_first_or_last_name,
)
@patch(
    "saleor.graphql.order.filters._filter_by_customer_full_name",
    wraps=_filter_by_customer_full_name,
)
def test_filter_customer_by_full_name_last_first_name(
    mock_filter_by_customer_full_name,
    mock_filter_customer_by_email_first_or_last_name,
    similar_customers_with_orders,
):
    # given
    order, order2, customer_user, customer_user2 = similar_customers_with_orders
    qs = Order.objects.all()
    value = f"{customer_user.last_name} {customer_user.first_name}"

    # when
    qs = filter_customer(qs, None, value)

    # then
    assert qs.count() == 1
    assert qs.first() == order
    mock_filter_by_customer_full_name.assert_called_once_with(ANY, value)
    mock_filter_customer_by_email_first_or_last_name.assert_not_called()


@patch(
    "saleor.graphql.order.filters._filter_customer_by_email_first_or_last_name",
    wraps=_filter_customer_by_email_first_or_last_name,
)
@patch(
    "saleor.graphql.order.filters._filter_by_customer_full_name",
    wraps=_filter_by_customer_full_name,
)
def test_filter_customer_by_email_domain(
    mock_filter_by_customer_full_name,
    mock_filter_customer_by_email_first_or_last_name,
    similar_customers_with_orders,
):
    # given
    order, order2, customer_user, customer_user2 = similar_customers_with_orders
    qs = Order.objects.all()
    value = customer_user.email.split("@")[1]

    # when
    qs = filter_customer(qs, None, value)

    # then
    assert qs.count() == 2
    assert order in qs
    assert order2 in qs
    mock_filter_by_customer_full_name.assert_called_once_with(ANY, value)
    mock_filter_customer_by_email_first_or_last_name.assert_called_once_with(ANY, value)
