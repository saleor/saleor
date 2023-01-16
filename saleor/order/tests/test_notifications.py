from decimal import Decimal
from functools import partial
from unittest import mock

import graphene
from django.core.files import File
from measurement.measures import Weight
from prices import Money, fixed_discount

from ...core.notify_events import NotifyEventType
from ...core.prices import quantize_price
from ...core.tests.utils import get_site_context_payload
from ...discount import DiscountValueType
from ...graphql.core.utils import to_global_id_or_none
from ...graphql.order.utils import OrderLineData
from ...order import notifications
from ...order.fetch import fetch_order_info
from ...plugins.manager import get_plugins_manager
from ...product.models import DigitalContentUrl
from ...thumbnail import THUMBNAIL_SIZES
from ...thumbnail.models import Thumbnail
from ..notifications import (
    get_address_payload,
    get_custom_order_payload,
    get_default_fulfillment_line_payload,
    get_default_fulfillment_payload,
    get_default_images_payload,
    get_default_order_payload,
    get_order_line_payload,
)
from ..utils import add_variant_to_order


def test_get_custom_order_payload(order, site_settings):
    expected_payload = get_custom_order_payload(order)
    assert expected_payload == {
        "order": {
            "id": to_global_id_or_none(order),
            "number": order.number,
            "private_metadata": {},
            "metadata": order.metadata,
            "status": "unfulfilled",
            "language_code": "en",
            "currency": "USD",
            "token": expected_payload["order"]["token"],
            "total_net_amount": 0,
            "undiscounted_total_net_amount": 0,
            "total_gross_amount": 0,
            "undiscounted_total_gross_amount": 0,
            "display_gross_prices": True,
            "channel_slug": "main",
            "created": expected_payload["order"]["created"],
            "shipping_price_net_amount": 0,
            "shipping_price_gross_amount": 0,
            "order_details_url": "",
            "email": "test@example.com",
            "subtotal_gross_amount": expected_payload["order"]["subtotal_gross_amount"],
            "subtotal_net_amount": expected_payload["order"]["subtotal_net_amount"],
            "tax_amount": 0,
            "lines": [],
            "billing_address": {
                "first_name": "John",
                "last_name": "Doe",
                "company_name": "Mirumee Software",
                "street_address_1": "Tęczowa 7",
                "street_address_2": "",
                "city": "WROCŁAW",
                "city_area": "",
                "postal_code": "53-601",
                "country": "PL",
                "country_area": "",
                "phone": "+48713988102",
            },
            "shipping_address": {
                "first_name": "John",
                "last_name": "Doe",
                "company_name": "Mirumee Software",
                "street_address_1": "Tęczowa 7",
                "street_address_2": "",
                "city": "WROCŁAW",
                "city_area": "",
                "postal_code": "53-601",
                "country": "PL",
                "country_area": "",
                "phone": "+48713988102",
            },
            "shipping_method_name": None,
            "collection_point_name": None,
            "voucher_discount": None,
            "discounts": [],
            "discount_amount": 0,
        },
        "recipient_email": "test@example.com",
        **get_site_context_payload(site_settings.site),
    }


def test_get_order_line_payload(order_line):
    order_line.variant.product.weight = Weight(kg=5)
    order_line.variant.product.save()

    payload = get_order_line_payload(order_line)

    attributes = order_line.variant.product.attributes.all()
    expected_attributes_payload = []
    for attr in attributes:
        expected_attributes_payload.append(
            {
                "assignment": {
                    "attribute": {
                        "slug": attr.assignment.attribute.slug,
                        "name": attr.assignment.attribute.name,
                    }
                },
                "values": [
                    {
                        "name": value.name,
                        "value": value.value,
                        "slug": value.slug,
                        "file_url": value.file_url,
                    }
                    for value in attr.values.all()
                ],
            }
        )
    unit_tax_amount = (
        order_line.unit_price_gross_amount - order_line.unit_price_net_amount
    )
    total_gross = order_line.unit_price_gross * order_line.quantity
    total_net = order_line.unit_price_net * order_line.quantity
    total_tax = total_gross - total_net
    currency = order_line.currency
    assert payload == {
        "variant": {
            "id": to_global_id_or_none(order_line.variant),
            "first_image": None,
            "images": None,
            "weight": "",
            "is_preorder": False,
            "preorder_global_threshold": None,
            "preorder_end_date": None,
        },
        "product": {
            "attributes": expected_attributes_payload,
            "first_image": None,
            "images": None,
            "weight": "5.0 kg",
            "id": to_global_id_or_none(order_line.variant.product),
        },
        "translated_product_name": order_line.translated_product_name
        or order_line.product_name,
        "translated_variant_name": order_line.translated_variant_name
        or order_line.variant_name,
        "id": to_global_id_or_none(order_line),
        "product_name": order_line.product_name,
        "variant_name": order_line.variant_name,
        "product_sku": order_line.product_sku,
        "product_variant_id": to_global_id_or_none(order_line.variant),
        "is_shipping_required": order_line.is_shipping_required,
        "quantity": order_line.quantity,
        "quantity_fulfilled": order_line.quantity_fulfilled,
        "currency": order_line.currency,
        "unit_price_net_amount": quantize_price(
            order_line.unit_price_net_amount, currency
        ),
        "unit_price_gross_amount": quantize_price(
            order_line.unit_price_gross_amount, currency
        ),
        "unit_tax_amount": quantize_price(unit_tax_amount, currency),
        "total_gross_amount": quantize_price(total_gross.amount, currency),
        "total_net_amount": quantize_price(total_net.amount, currency),
        "total_tax_amount": quantize_price(total_tax.amount, currency),
        "tax_rate": order_line.tax_rate,
        "is_digital": order_line.is_digital,
        "digital_url": None,
        "unit_discount_amount": order_line.unit_discount_amount,
        "unit_discount_reason": order_line.unit_discount_reason,
        "unit_discount_type": order_line.unit_discount_type,
        "unit_discount_value": order_line.unit_discount_value,
        "metadata": order_line.metadata,
    }


def test_get_order_line_payload_deleted_variant(order_line):
    order_line.variant = None
    payload = get_order_line_payload(order_line)

    assert payload["variant"] is None
    assert payload["product"] is None


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
    subtotal = order.get_subtotal()
    order.total = subtotal + order.shipping_price
    tax = order.total_gross_amount - order.total_net_amount

    value = Decimal("20")
    discount = partial(fixed_discount, discount=Money(value, order.currency))
    order.undiscounted_total = order.total
    order.total = discount(order.total)
    order.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=value,
        reason="Discount reason",
        amount=(order.undiscounted_total - order.total).gross,
    )
    order.save()

    payload = get_default_order_payload(order, redirect_url)

    assert payload == {
        "discounts": [
            {
                "amount_value": Decimal("20.000"),
                "name": None,
                "reason": "Discount reason",
                "translated_name": None,
                "type": "manual",
                "value": Decimal("20.000"),
                "value_type": "fixed",
            }
        ],
        "channel_slug": order.channel.slug,
        "id": to_global_id_or_none(order),
        "number": order.number,
        "token": order.id,
        "created": str(order.created_at),
        "display_gross_prices": order.display_gross_prices,
        "currency": order.currency,
        "total_gross_amount": order.total_gross_amount,
        "total_net_amount": order.total_net_amount,
        "shipping_method_name": order.shipping_method_name,
        "collection_point_name": order.collection_point_name,
        "status": order.status,
        "metadata": order.metadata,
        "private_metadata": {},
        "shipping_price_net_amount": order.shipping_price_net_amount,
        "shipping_price_gross_amount": order.shipping_price_gross_amount,
        "order_details_url": f"{redirect_url}?token={order.id}",
        "email": order.get_customer_email(),
        "subtotal_gross_amount": subtotal.gross.amount,
        "subtotal_net_amount": subtotal.net.amount,
        "tax_amount": tax,
        "lines": [order_line_payload],
        "billing_address": get_address_payload(order.billing_address),
        "shipping_address": get_address_payload(order.shipping_address),
        "language_code": order.language_code,
        "discount_amount": Decimal("20.000"),
        "undiscounted_total_gross_amount": order.undiscounted_total.gross.amount,
        "undiscounted_total_net_amount": order.undiscounted_total.net.amount,
        "voucher_discount": None,
    }


def test_get_default_fulfillment_payload(fulfillment, digital_content, site_settings):
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
    payload["order"]["lines"] = sorted(
        payload["order"]["lines"], key=lambda line: line["id"]
    )
    payload["physical_lines"] = sorted(
        payload["physical_lines"], key=lambda line: line["id"]
    )
    order_payload["lines"] = sorted(order_payload["lines"], key=lambda line: line["id"])

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
        "recipient_email": order.get_customer_email(),
        **get_site_context_payload(site_settings.site),
    }


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_email_payment_confirmation(mocked_notify, site_settings, payment_dummy):
    manager = get_plugins_manager()
    order = payment_dummy.order
    order_info = fetch_order_info(order)
    expected_payload = {
        "order": get_default_order_payload(order),
        "recipient_email": order.get_customer_email(),
        "payment": {
            "created": payment_dummy.created_at,
            "modified": payment_dummy.modified_at,
            "charge_status": payment_dummy.charge_status,
            "total": payment_dummy.total,
            "captured_amount": payment_dummy.captured_amount,
            "currency": payment_dummy.currency,
        },
        **get_site_context_payload(site_settings.site),
    }
    notifications.send_payment_confirmation(order_info, manager)
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_PAYMENT_CONFIRMATION,
        expected_payload,
        channel_slug=order.channel.slug,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_email_order_confirmation(mocked_notify, order, site_settings):
    manager = get_plugins_manager()
    redirect_url = "https://www.example.com"
    order_info = fetch_order_info(order)

    notifications.send_order_confirmation(order_info, redirect_url, manager)

    expected_payload = {
        "order": get_default_order_payload(order, redirect_url),
        "recipient_email": order.get_customer_email(),
        **get_site_context_payload(site_settings.site),
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_CONFIRMATION,
        expected_payload,
        channel_slug=order.channel.slug,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_email_order_confirmation_for_cc(
    mocked_notify, order_with_lines_for_cc, site_settings, warehouse_for_cc
):
    manager = get_plugins_manager()
    redirect_url = "https://www.example.com"
    order_info = fetch_order_info(order_with_lines_for_cc)

    notifications.send_order_confirmation(order_info, redirect_url, manager)

    expected_payload = {
        "order": get_default_order_payload(order_with_lines_for_cc, redirect_url),
        "recipient_email": order_with_lines_for_cc.get_customer_email(),
        **get_site_context_payload(site_settings.site),
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_CONFIRMATION,
        expected_payload,
        channel_slug=order_with_lines_for_cc.channel.slug,
    )
    assert expected_payload["order"]["collection_point_name"] == warehouse_for_cc.name


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_confirmation_emails_without_addresses_for_payment(
    mocked_notify,
    site_settings,
    anonymous_plugins,
    digital_content,
    payment_dummy,
):
    order = payment_dummy.order
    line_data = OrderLineData(
        variant_id=str(digital_content.product_variant.id),
        variant=digital_content.product_variant,
        quantity=1,
    )

    line = add_variant_to_order(
        order=order,
        line_data=line_data,
        user=None,
        app=None,
        manager=anonymous_plugins,
    )
    DigitalContentUrl.objects.create(content=digital_content, line=line)

    order.shipping_address = None
    order.shipping_method = None
    order.billing_address = None
    order.save(update_fields=["shipping_address", "shipping_method", "billing_address"])
    order_info = fetch_order_info(order)

    notifications.send_payment_confirmation(order_info, anonymous_plugins)

    expected_payload = {
        "order": get_default_order_payload(order),
        "recipient_email": order.get_customer_email(),
        "payment": {
            "created": payment_dummy.created_at,
            "modified": payment_dummy.modified_at,
            "charge_status": payment_dummy.charge_status,
            "total": payment_dummy.total,
            "captured_amount": payment_dummy.captured_amount,
            "currency": payment_dummy.currency,
        },
        **get_site_context_payload(site_settings.site),
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_PAYMENT_CONFIRMATION,
        expected_payload,
        channel_slug=order.channel.slug,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_confirmation_emails_without_addresses_for_order(
    mocked_notify,
    order,
    site_settings,
    digital_content,
    anonymous_plugins,
):

    assert not order.lines.count()
    line_data = OrderLineData(
        variant_id=str(digital_content.product_variant.id),
        variant=digital_content.product_variant,
        quantity=1,
    )

    line = add_variant_to_order(
        order=order,
        line_data=line_data,
        user=None,
        app=None,
        manager=anonymous_plugins,
    )
    DigitalContentUrl.objects.create(content=digital_content, line=line)

    order.shipping_address = None
    order.shipping_method = None
    order.billing_address = None
    order.save(update_fields=["shipping_address", "shipping_method", "billing_address"])
    order_info = fetch_order_info(order)

    redirect_url = "https://www.example.com"

    notifications.send_order_confirmation(order_info, redirect_url, anonymous_plugins)

    expected_payload = {
        "order": get_default_order_payload(order, redirect_url),
        "recipient_email": order.get_customer_email(),
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_CONFIRMATION,
        expected_payload,
        channel_slug=order.channel.slug,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_fulfillment_confirmation_by_user(
    mocked_notify, fulfilled_order, site_settings, staff_user
):
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.tracking_number = "https://www.example.com"
    fulfillment.save()
    manager = get_plugins_manager()

    notifications.send_fulfillment_confirmation_to_customer(
        order=fulfilled_order,
        fulfillment=fulfillment,
        user=staff_user,
        app=None,
        manager=manager,
    )

    expected_payload = get_default_fulfillment_payload(fulfilled_order, fulfillment)
    expected_payload["requester_user_id"] = to_global_id_or_none(staff_user)
    expected_payload["requester_app_id"] = None
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_FULFILLMENT_CONFIRMATION,
        payload=expected_payload,
        channel_slug=fulfilled_order.channel.slug,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_fulfillment_confirmation_by_app(
    mocked_notify, fulfilled_order, site_settings, app
):
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.tracking_number = "https://www.example.com"
    fulfillment.save()
    manager = get_plugins_manager()

    notifications.send_fulfillment_confirmation_to_customer(
        order=fulfilled_order,
        fulfillment=fulfillment,
        user=None,
        app=app,
        manager=manager,
    )

    expected_payload = get_default_fulfillment_payload(fulfilled_order, fulfillment)
    expected_payload["requester_user_id"] = None
    expected_payload["requester_app_id"] = to_global_id_or_none(app)
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_FULFILLMENT_CONFIRMATION,
        payload=expected_payload,
        channel_slug=fulfilled_order.channel.slug,
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
        NotifyEventType.ORDER_FULFILLMENT_UPDATE,
        expected_payload,
        channel_slug=fulfilled_order.channel.slug,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_email_order_canceled_by_user(
    mocked_notify, order, site_settings, staff_user
):
    # given
    manager = get_plugins_manager()

    # when
    notifications.send_order_canceled_confirmation(order, staff_user, None, manager)

    # then
    expected_payload = {
        "order": get_default_order_payload(order),
        "recipient_email": order.get_customer_email(),
        "requester_user_id": to_global_id_or_none(staff_user),
        "requester_app_id": None,
        **get_site_context_payload(site_settings.site),
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_CANCELED,
        expected_payload,
        channel_slug=order.channel.slug,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_email_order_canceled_by_app(mocked_notify, order, site_settings, app):
    # given
    manager = get_plugins_manager()

    # when
    notifications.send_order_canceled_confirmation(order, None, app, manager)

    # then
    expected_payload = {
        "order": get_default_order_payload(order),
        "recipient_email": order.get_customer_email(),
        "requester_user_id": None,
        "requester_app_id": to_global_id_or_none(app),
        **get_site_context_payload(site_settings.site),
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_CANCELED,
        expected_payload,
        channel_slug=order.channel.slug,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_email_order_refunded_by_user(
    mocked_notify, order, site_settings, staff_user
):
    # given
    manager = get_plugins_manager()
    amount = order.total.gross.amount

    # when
    notifications.send_order_refunded_confirmation(
        order, staff_user, None, amount, order.currency, manager
    )

    # then
    expected_payload = {
        "requester_user_id": to_global_id_or_none(staff_user),
        "requester_app_id": None,
        "order": get_default_order_payload(order),
        "amount": amount,
        "currency": order.currency,
        "recipient_email": order.get_customer_email(),
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_REFUND_CONFIRMATION,
        expected_payload,
        channel_slug=order.channel.slug,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_email_order_refunded_by_app(mocked_notify, order, site_settings, app):
    # given
    manager = get_plugins_manager()
    amount = order.total.gross.amount

    # when
    notifications.send_order_refunded_confirmation(
        order, None, app, amount, order.currency, manager
    )

    # then
    expected_payload = {
        "requester_user_id": None,
        "requester_app_id": to_global_id_or_none(app),
        "order": get_default_order_payload(order),
        "amount": amount,
        "currency": order.currency,
        "recipient_email": order.get_customer_email(),
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ORDER_REFUND_CONFIRMATION,
        expected_payload,
        channel_slug=order.channel.slug,
    )


def test_get_default_images_payload(product_with_image):
    # given
    size = 128

    thumbnail_mock = mock.MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"

    media = product_with_image.media.first()
    Thumbnail.objects.create(product_media=media, image=thumbnail_mock, size=size)

    media_id = graphene.Node.to_global_id("ProductMedia", media.id)

    # when
    payload = get_default_images_payload([media])

    # then
    images_payload = payload["first_image"]["original"]
    for th_size in THUMBNAIL_SIZES:
        assert images_payload[th_size] == f"/thumbnail/{media_id}/{th_size}/"
