from unittest import mock

from ..migrations.tasks.saleor3_21 import (
    BILLING_FIELD,
    SHIPPING_FIELD,
    fix_shared_address_instances_task,
)
from ..models import Checkout


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
