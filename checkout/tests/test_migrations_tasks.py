from decimal import Decimal
from unittest import mock

from ..migrations.tasks.saleor3_21 import (
    BILLING_FIELD,
    SHIPPING_FIELD,
    fix_shared_address_instances_task,
)
from ..migrations.tasks.saleor3_23 import propagate_checkout_deliveries_task
from ..models import Checkout, CheckoutDelivery


def test_fix_shared_billing_addresses(checkouts_list, order, address, address_usa):
    # given
    checkout1 = checkouts_list[0]
    checkout2 = checkouts_list[1]
    checkout3 = checkouts_list[2]

    # these two share address with order
    checkout1.billing_address = address
    checkout2.billing_address = address
    new_checkout_address = address.get_copy()
    checkout1.shipping_address = new_checkout_address
    checkout2.shipping_address = new_checkout_address
    # this one has unique address
    checkout3.billing_address = address_usa
    Checkout.objects.bulk_update(
        [checkout1, checkout2, checkout3], ["billing_address", "shipping_address"]
    )

    order.billing_address = address
    new_order_address = address.get_copy()
    order.shipping_address = new_order_address
    order.save(update_fields=["billing_address", "shipping_address"])

    # when
    fix_shared_address_instances_task()

    # then
    for checkout in [checkout1, checkout2]:
        checkout.refresh_from_db()
        assert checkout.billing_address_id != address.id
        assert checkout.billing_address.as_data() == address.as_data()
        assert checkout.shipping_address_id == new_checkout_address.id

    checkout3.refresh_from_db()
    assert checkout3.billing_address_id == address_usa.id


def test_fix_shared_shipping_addresses(checkouts_list, order, address, address_usa):
    # given
    checkout1 = checkouts_list[0]
    checkout2 = checkouts_list[1]
    checkout3 = checkouts_list[2]

    # these two share address with order
    checkout1.shipping_address = address
    checkout2.shipping_address = address
    new_checkout_address = address.get_copy()
    checkout1.billing_address = new_checkout_address
    checkout2.billing_address = new_checkout_address
    # this one has unique address
    checkout3.shipping_address = address_usa
    Checkout.objects.bulk_update(
        [checkout1, checkout2, checkout3], ["shipping_address", "billing_address"]
    )

    new_order_address = address.get_copy()
    order.billing_address = new_order_address
    order.shipping_address = address
    order.save(update_fields=["shipping_address", "billing_address"])

    # when
    fix_shared_address_instances_task(field=SHIPPING_FIELD)

    # then
    for checkout in [checkout1, checkout2]:
        checkout.refresh_from_db()
        assert checkout.shipping_address_id != address.id
        assert checkout.shipping_address.as_data() == address.as_data()
        assert checkout.billing_address_id == new_checkout_address.id

    checkout3.refresh_from_db()
    assert checkout3.shipping_address_id == address_usa.id


def test_no_checkouts_with_shared_addresses(checkout, order, address):
    # given
    checkout.billing_address = address
    checkout.save(update_fields=["billing_address"])

    # address linked to order is different instance, but same data
    order_address = address.get_copy()
    order.billing_address = order_address
    order.save(update_fields=["billing_address"])

    assert checkout.billing_address_id != order.billing_address_id

    # when
    fix_shared_address_instances_task()

    # then
    checkout.refresh_from_db()
    assert checkout.billing_address_id == address.id


@mock.patch(
    "saleor.checkout.migrations.tasks.saleor3_21.fix_shared_address_instances_task.delay"
)
def test_task_switches_fields(mock_delay, checkout, order, address):
    # given
    # only shared shipping address exists
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    order.shipping_address = address
    order.save(update_fields=["shipping_address"])

    # when
    # Trigger with default billing field
    fix_shared_address_instances_task()

    # then
    # Should call itself with shipping field because no billing addresses were found to fix
    mock_delay.assert_called_once_with(field=SHIPPING_FIELD)


@mock.patch("saleor.checkout.migrations.tasks.saleor3_21.BATCH_SIZE", 1)
@mock.patch(
    "saleor.checkout.migrations.tasks.saleor3_21.fix_shared_address_instances_task.delay"
)
def test_task_recursion(mock_delay, checkouts_list, order, address):
    # given
    # we have 2 checkouts sharing same address with order
    # batch size is 1, so it should process first checkout and then call delay
    checkout1 = checkouts_list[0]
    checkout2 = checkouts_list[1]

    order.billing_address = address
    order.save(update_fields=["billing_address"])

    checkout1.billing_address = address
    checkout2.billing_address = address
    Checkout.objects.bulk_update([checkout1, checkout2], ["billing_address"])

    # when
    fix_shared_address_instances_task()

    # then
    checkout1.refresh_from_db()
    checkout2.refresh_from_db()

    # only one should be fixed in first batch
    fixed_checkouts = [
        c for c in [checkout1, checkout2] if c.billing_address_id != address.id
    ]
    assert len(fixed_checkouts) == 1

    # ensure it triggered next batch
    mock_delay.assert_called_once_with(field=BILLING_FIELD)


@mock.patch(
    "saleor.checkout.migrations.tasks.saleor3_23.propagate_checkout_deliveries_task.delay"
)
def test_propagate_checkout_built_in_delivery(
    mocked_task_delay, checkout, shipping_method
):
    # given
    expected_price = Decimal(10.00)
    checkout.shipping_method = shipping_method
    checkout.shipping_method_name = shipping_method.name
    checkout.undiscounted_base_shipping_price_amount = expected_price
    checkout.save()
    assert not checkout.assigned_delivery_id

    # when
    propagate_checkout_deliveries_task()

    # then
    checkout.refresh_from_db()
    assert checkout.assigned_delivery
    delivery = checkout.assigned_delivery
    assert delivery.built_in_shipping_method_id == shipping_method.id
    assert delivery.name == shipping_method.name
    assert delivery.price_amount == expected_price
    assert delivery.currency == checkout.currency
    assert not delivery.is_external
    assert delivery.active
    assert delivery.tax_class_id == shipping_method.tax_class.id
    assert delivery.tax_class_name == shipping_method.tax_class.name
    assert mocked_task_delay.called


@mock.patch(
    "saleor.checkout.migrations.tasks.saleor3_23.propagate_checkout_deliveries_task.delay"
)
def test_propagate_checkout_external_delivery(
    mocked_task_delay,
    checkout,
):
    # given
    external_shipping_method_id = "external-id"
    external_shipping_name = "External shipping"
    expected_price = Decimal(10.00)
    checkout.external_shipping_method_id = external_shipping_method_id
    checkout.shipping_method_name = external_shipping_name
    checkout.undiscounted_base_shipping_price_amount = expected_price
    checkout.save()
    assert not checkout.assigned_delivery_id

    # when
    propagate_checkout_deliveries_task()

    # then
    checkout.refresh_from_db()
    assert checkout.assigned_delivery
    delivery = checkout.assigned_delivery
    assert delivery.external_shipping_method_id == external_shipping_method_id
    assert delivery.name == external_shipping_name
    assert delivery.price_amount == expected_price
    assert delivery.currency == checkout.currency
    assert delivery.is_external
    assert delivery.active
    assert mocked_task_delay.called


@mock.patch(
    "saleor.checkout.migrations.tasks.saleor3_23.propagate_checkout_deliveries_task.delay"
)
def test_propagate_checkout_delivery_handles_duplicated_deliveries(
    mocked_task_delay, checkout, shipping_method, checkout_delivery
):
    # given
    expected_price = Decimal(10.00)
    checkout.shipping_method = shipping_method
    checkout.shipping_method_name = shipping_method.name
    checkout.undiscounted_base_shipping_price_amount = expected_price
    checkout.save()
    assert not checkout.assigned_delivery_id

    # Cover the case when delivery was created in the background
    checkout_delivery(checkout, shipping_method)
    assert CheckoutDelivery.objects.get()

    # when
    propagate_checkout_deliveries_task()

    # then
    checkout.refresh_from_db()
    assert checkout.assigned_delivery
    delivery = checkout.assigned_delivery
    assert delivery.built_in_shipping_method_id == shipping_method.id
    assert delivery.name == shipping_method.name
    assert delivery.price_amount == expected_price
    assert delivery.currency == checkout.currency
    assert not delivery.is_external
    assert delivery.active
    assert delivery.tax_class_id == shipping_method.tax_class.id
    assert delivery.tax_class_name == shipping_method.tax_class.name
    assert mocked_task_delay.called


@mock.patch(
    "saleor.checkout.migrations.tasks.saleor3_23.propagate_checkout_deliveries_task.delay"
)
def test_propagate_checkout_delivery_built_in_when_no_valid_checkouts(
    mocked_task_delay, checkout, shipping_method, checkout_delivery
):
    # given
    expected_price = Decimal(10.00)
    checkout.shipping_method = shipping_method
    checkout.shipping_method_name = shipping_method.name
    checkout.undiscounted_base_shipping_price_amount = expected_price
    delivery = checkout_delivery(checkout, shipping_method)
    checkout.assigned_delivery = delivery
    checkout.save()

    assert not Checkout.objects.filter(
        shipping_method_id__isnull=False, assigned_delivery__isnull=True
    ).exists()

    # when
    propagate_checkout_deliveries_task()

    # then
    checkout.refresh_from_db()
    assert checkout.assigned_delivery == delivery
    assert not mocked_task_delay.called


@mock.patch(
    "saleor.checkout.migrations.tasks.saleor3_23.propagate_checkout_deliveries_task.delay"
)
def test_propagate_checkout_delivery_external_when_no_valid_checkouts(
    mocked_task_delay, checkout, shipping_method, checkout_delivery
):
    # given
    external_shipping_method_id = "external-id"
    external_shipping_name = "External shipping"
    expected_price = Decimal(10.00)
    checkout.external_shipping_method_id = external_shipping_method_id
    checkout.shipping_method_name = external_shipping_name
    checkout.undiscounted_base_shipping_price_amount = expected_price
    delivery = CheckoutDelivery.objects.create(
        external_shipping_method_id=external_shipping_method_id,
        name=external_shipping_name,
        price_amount=expected_price,
        currency=checkout.currency,
        is_external=True,
        checkout=checkout,
    )
    checkout.assigned_delivery = delivery
    checkout.save()

    assert not Checkout.objects.filter(
        external_shipping_method_id__isnull=False, assigned_delivery__isnull=True
    ).exists()

    # when
    propagate_checkout_deliveries_task()

    # then
    checkout.refresh_from_db()
    assert checkout.assigned_delivery == delivery
    assert not mocked_task_delay.called
