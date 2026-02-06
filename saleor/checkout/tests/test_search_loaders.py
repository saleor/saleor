from decimal import Decimal

from ...payment.models import Payment, TransactionItem
from ..search.loaders import load_checkout_data


def test_load_checkout_data(checkout_with_item, customer_user, address, address_usa):
    # given
    checkout_with_item.user = customer_user
    checkout_with_item.billing_address = address
    checkout_with_item.shipping_address = address_usa
    checkout_with_item.save()

    Payment.objects.create(
        gateway="mirumee.payments.dummy",
        is_active=True,
        checkout=checkout_with_item,
        total=Decimal("10.00"),
        currency="USD",
    )

    TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP-123",
        available_actions=["refund"],
        currency="USD",
        checkout_id=checkout_with_item.pk,
        charged_value=Decimal(10),
    )

    # when
    result = load_checkout_data([checkout_with_item])

    # then
    assert checkout_with_item.pk in result
    checkout_data = result[checkout_with_item.pk]
    assert checkout_data.user == customer_user
    assert checkout_data.billing_address == address
    assert checkout_data.shipping_address == address_usa
    assert len(checkout_data.payments) == 1
    assert len(checkout_data.lines) == checkout_with_item.lines.count()
    assert len(checkout_data.transactions) == 1


def test_load_checkout_data_empty_list():
    # given
    checkouts = []

    # when
    result = load_checkout_data(checkouts)

    # then
    assert result == {}


def test_load_checkout_data_with_no_relations(checkout):
    # given
    checkout.user = None
    checkout.billing_address = None
    checkout.shipping_address = None
    checkout.save()

    # when
    result = load_checkout_data([checkout])

    # then
    assert checkout.pk in result
    checkout_data = result[checkout.pk]
    assert checkout_data.user is None
    assert checkout_data.billing_address is None
    assert checkout_data.shipping_address is None
    assert checkout_data.payments == []
    assert checkout_data.lines == []
    assert checkout_data.transactions == []


def test_load_checkout_data_multiple_checkouts(checkout_with_item, checkout_JPY):
    # given
    checkouts = [checkout_with_item, checkout_JPY]

    # when
    result = load_checkout_data(checkouts)

    # then
    assert len(result) == 2
    assert checkout_with_item.pk in result
    assert checkout_JPY.pk in result
