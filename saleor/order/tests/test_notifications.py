from unittest import mock

from ...core.notify_events import NotifyEventType
from ...order import notifications
from ...plugins.manager import get_plugins_manager
from ...product.models import DigitalContentUrl
from ..notifications import (
    get_address_payload,
    get_default_fulfillment_line_payload,
    get_default_fulfillment_payload,
    get_default_order_payload,
    get_order_line_payload,
)
from ..utils import add_variant_to_draft_order


def test_get_order_line_payload(order_line):
    payload = get_order_line_payload(order_line)
    unit_tax_amount = (
        order_line.unit_price_gross_amount - order_line.unit_price_net_amount,
    )
    total_gross = order_line.unit_price_gross * order_line.quantity
    total_net = order_line.unit_price_net * order_line.quantity
    total_tax = total_gross - total_net
    assert payload == {
        "id": order_line.id,
        "product_name": order_line.translated_product_name or order_line.product_name,
        "variant_name": order_line.translated_variant_name or order_line.variant_name,
        "product_sku": order_line.product_sku,
        "is_shipping_required": order_line.is_shipping_required,
        "quantity": order_line.quantity,
        "quantity_fulfilled": order_line.quantity_fulfilled,
        "currency": order_line.currency,
        "unit_price_net_amount": order_line.unit_price_net_amount,
        "unit_price_gross_amount": order_line.unit_price_gross_amount,
        "unit_tax_amount": unit_tax_amount,
        "total_gross_amount": total_gross.amount,
        "total_net_amount": total_net.amount,
        "total_tax_amount": total_tax.amount,
        "tax_rate": order_line.tax_rate,
        "is_digital": order_line.is_digital,
        "digital_url": "",
    }


def test_get_address_payload(address):
    payload = get_address_payload(address)
    assert payload == {
        "first_name": address.first_name,
        "last_name": address.last_name,
        "company_name": address.company_name,
        "street_address_1": address.street_address_1,
        "street_address_2": address.street_address_2,
        "city": address.city,
        "city_area": address.city_area,
        "postal_code": address.postal_code,
        "country": str(address.country),
        "country_area": address.country_area,
        "phone": str(address.phone),
    }


def test_get_default_order_payload(order_line):
    order_line.refresh_from_db()
    order = order_line.order
    order_line_payload = get_order_line_payload(order_line)
    redirect_url = "http://redirect.com/path"
    payload = get_default_order_payload(order, redirect_url)
    subtotal = order.get_subtotal()
    tax = order.total_gross_amount - order.total_net_amount
    assert payload == {
        "id": order.id,
        "token": order.token,
        "created": order.created,
        "display_gross_prices": order.display_gross_prices,
        "currency": order.currency,
        "discount_amount": order.discount_amount,
        "total_gross_amount": order.total_gross_amount,
        "total_net_amount": order.total_net_amount,
        "shipping_method_name": order.shipping_method_name,
        "status": order.status,
        "metadata": order.metadata,
        "private_metadata": order.private_metadata,
        "shipping_price_net_amount": order.shipping_price_net_amount,
        "shipping_price_gross_amount": order.shipping_price_gross_amount,
        "order_details_url": f"{redirect_url}?token={order.token}",
        "email": order.get_customer_email(),
        "subtotal_gross_amount": subtotal.gross.amount,
        "subtotal_net_amount": subtotal.net.amount,
        "tax_amount": tax,
        "discount_name": order.translated_discount_name or order.discount_name,
        "lines": [order_line_payload],
        "billing_address": get_address_payload(order.billing_address),
        "shipping_address": get_address_payload(order.shipping_address),
    }


def test_get_default_fulfillment_payload(
    fulfillment, digital_content,
):
    order = fulfillment.order
    fulfillment.tracking_number = "http://tracking.url.com/123"
    fulfillment.save(update_fields=["tracking_number"])
    line = order.lines.first()
    line.variant = digital_content.product_variant
    line.save(update_fields=["variant"])
    DigitalContentUrl.objects.create(content=digital_content, line=line)

    order_payload = get_default_order_payload(order)
    payload = get_default_fulfillment_payload(order, fulfillment)

    # make sure that test will not fail because of the list order
    payload["order"]["lines"] = sorted(payload["order"]["lines"], key=lambda l: l["id"])
    payload["physical_lines"] = sorted(payload["physical_lines"], key=lambda l: l["id"])
    order_payload["lines"] = sorted(order_payload["lines"], key=lambda l: l["id"])

    digital_line = fulfillment.lines.get(order_line=line.id)
    physical_line = fulfillment.lines.exclude(id=digital_line.id).first()
    assert payload == {
        "order": order_payload,
        "fulfillment": {
            "tracking_number": fulfillment.tracking_number,
            "is_tracking_number_url": fulfillment.is_tracking_number_url,
        },
        "physical_lines": [get_default_fulfillment_line_payload(physical_line)],
        "digital_lines": [get_default_fulfillment_line_payload(digital_line)],
        "email": order.get_customer_email(),
    }


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_email_payment_confirmation(mocked_notify, site_settings, payment_dummy):
    manager = get_plugins_manager()
    order = payment_dummy.order
    expected_payload = {
        "order": get_default_order_payload(order),
        "email": order.get_customer_email(),
        "payment": {
            "created": payment_dummy.created,
            "modified": payment_dummy.modified,
            "charge_status": payment_dummy.charge_status,
            "total": payment_dummy.total,
            "captured_amount": payment_dummy.captured_amount,
            "currency": payment_dummy.currency,
        },
    }
    notifications.send_payment_confirmation(order, manager)
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_PAYMENT_CONFIRMATION, expected_payload
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_staff_emails_without_notification_recipient(
    mocked_notify, order, site_settings
):
    manager = get_plugins_manager()
    notifications.send_staff_order_confirmation(
        order, "http://www.example.com/", manager
    )
    mocked_notify.assert_not_called()


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_staff_emails(
    mocked_notify, order, site_settings, staff_notification_recipient
):
    manager = get_plugins_manager()
    redirect_url = "http://www.example.com/"
    notifications.send_staff_order_confirmation(order, redirect_url, manager)
    expected_payload = {
        "order": get_default_order_payload(order, redirect_url),
        "recipient_list": [staff_notification_recipient.get_email()],
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.STAFF_ORDER_CONFIRMATION, payload=expected_payload
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_email_order_confirmation(mocked_notify, order, site_settings):
    manager = get_plugins_manager()
    redirect_url = "https://www.example.com"

    notifications.send_order_confirmation(order, redirect_url, order.user, manager)

    expected_payload = get_default_order_payload(order, redirect_url)
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_CONFIRMATION, expected_payload
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_confirmation_emails_without_addresses_for_payment(
    mocked_notify, site_settings, digital_content, payment_dummy,
):
    order = payment_dummy.order

    line = add_variant_to_draft_order(
        order, digital_content.product_variant, quantity=1
    )
    DigitalContentUrl.objects.create(content=digital_content, line=line)

    order.shipping_address = None
    order.shipping_method = None
    order.billing_address = None
    order.save(update_fields=["shipping_address", "shipping_method", "billing_address"])

    manager = get_plugins_manager()
    notifications.send_payment_confirmation(order, manager)

    expected_payload = {
        "order": get_default_order_payload(order),
        "email": order.get_customer_email(),
        "payment": {
            "created": payment_dummy.created,
            "modified": payment_dummy.modified,
            "charge_status": payment_dummy.charge_status,
            "total": payment_dummy.total,
            "captured_amount": payment_dummy.captured_amount,
            "currency": payment_dummy.currency,
        },
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_PAYMENT_CONFIRMATION, expected_payload
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_confirmation_emails_without_addresses_for_order(
    mocked_notify, order, site_settings, digital_content
):

    assert not order.lines.count()

    line = add_variant_to_draft_order(
        order, digital_content.product_variant, quantity=1
    )
    DigitalContentUrl.objects.create(content=digital_content, line=line)

    order.shipping_address = None
    order.shipping_method = None
    order.billing_address = None
    order.save(update_fields=["shipping_address", "shipping_method", "billing_address"])

    redirect_url = "https://www.example.com"
    manager = get_plugins_manager()

    notifications.send_order_confirmation(order, redirect_url, order.user, manager)

    expected_payload = get_default_order_payload(order, redirect_url)

    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_CONFIRMATION, expected_payload
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_fulfillment_confirmation(mocked_notify, fulfilled_order, site_settings):
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.tracking_number = "https://www.example.com"
    fulfillment.save()
    manager = get_plugins_manager()

    notifications.send_fulfillment_confirmation_to_customer(
        order=fulfilled_order,
        fulfillment=fulfillment,
        user=fulfilled_order.user,
        manager=manager,
    )

    expected_payload = get_default_fulfillment_payload(fulfilled_order, fulfillment)

    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_FULFILLMENT_CONFIRMATION, payload=expected_payload
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_fulfillment_update(mocked_notify, fulfilled_order, site_settings):
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.tracking_number = "https://www.example.com"
    fulfillment.save()
    manager = get_plugins_manager()

    notifications.send_fulfillment_update(
        order=fulfilled_order, fulfillment=fulfillment, manager=manager
    )

    expected_payload = get_default_fulfillment_payload(fulfilled_order, fulfillment)

    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_FULFILLMENT_UPDATE, expected_payload
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_email_order_canceled(mocked_notify, order, site_settings):
    # given
    manager = get_plugins_manager()

    # when
    notifications.send_order_canceled_confirmation(order, order.user, manager)

    # then
    expected_payload = {
        "order": get_default_order_payload(order),
        "email": order.get_customer_email(),
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_CANCELED, expected_payload
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_email_order_refunded(mocked_notify, order, site_settings):
    # given
    manager = get_plugins_manager()
    amount = order.total.gross.amount

    # when
    notifications.send_order_refunded_confirmation(
        order, order.user, amount, order.currency, manager
    )

    # then
    expected_payload = get_default_order_payload(order)
    expected_payload.update({"amount": amount, "currency": order.currency})

    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_REFUND_CONFIRMATION, expected_payload
    )
