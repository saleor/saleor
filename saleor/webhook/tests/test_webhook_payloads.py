import datetime
import json
from dataclasses import asdict
from decimal import Decimal
from itertools import chain
from unittest import mock
from unittest.mock import ANY, patch, sentinel

import graphene
import pytest
from django.core.serializers.json import DjangoJSONEncoder
from freezegun import freeze_time
from measurement.measures import Weight
from prices import Money

from ... import __version__
from ...checkout import base_calculations
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...checkout.models import CheckoutLine
from ...checkout.utils import add_voucher_to_checkout
from ...core.prices import quantize_price
from ...core.utils.json_serializer import CustomJsonEncoder
from ...discount import DiscountType, DiscountValueType, RewardValueType, VoucherType
from ...discount.models import CheckoutDiscount, CheckoutLineDiscount
from ...graphql.utils import get_user_or_app_from_context
from ...order import FulfillmentLineData, OrderOrigin
from ...order.actions import fulfill_order_lines
from ...order.fetch import OrderLineInfo
from ...order.models import Order
from ...payment import TransactionAction, TransactionEventType
from ...payment.interface import RefundData, TransactionActionData, TransactionData
from ...payment.models import TransactionItem
from ...plugins.manager import get_plugins_manager
from ...product.models import ProductVariant, ProductVariantChannelListing
from ...shipping.interface import ShippingMethodData
from ...warehouse import WarehouseClickAndCollectOption
from ..payloads import (
    PRODUCT_VARIANT_FIELDS,
    _generate_collection_point_payload,
    _generate_refund_data_payload,
    generate_checkout_payload,
    generate_checkout_payload_for_tax_calculation,
    generate_collection_payload,
    generate_customer_payload,
    generate_excluded_shipping_methods_for_checkout_payload,
    generate_excluded_shipping_methods_for_order_payload,
    generate_fulfillment_lines_payload,
    generate_invoice_payload,
    generate_list_gateways_payload,
    generate_meta,
    generate_metadata_updated_payload,
    generate_order_payload,
    generate_order_payload_for_tax_calculation,
    generate_payment_payload,
    generate_product_media_payload,
    generate_product_payload,
    generate_product_variant_payload,
    generate_product_variant_with_stock_payload,
    generate_requestor,
    generate_sale_payload,
    generate_sale_toggle_payload,
    generate_thumbnail_payload,
    generate_transaction_action_request_payload,
    generate_translation_payload,
)
from ..serializers import serialize_checkout_lines
from ..transport.utils import from_payment_app_id


def parse_django_datetime(date):
    return json.loads(json.dumps(date, cls=DjangoJSONEncoder))


@pytest.fixture
def order_for_payload(fulfilled_order, voucher_percentage):
    order = fulfilled_order

    new_order = Order.objects.create(
        channel=order.channel,
        billing_address=order.billing_address,
        lines_count=0,
    )
    order.origin = OrderOrigin.REISSUE
    order.original = new_order
    order.save(update_fields=["origin", "original"])

    order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=Decimal(20),
        amount_value=Decimal("33.0"),
        reason="Discount from staff",
    )
    discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=Decimal(10),
        amount_value=Decimal("16.5"),
        name="Voucher",
        voucher=voucher_percentage,
    )

    discount.created_at = datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(
        days=1
    )
    discount.save(update_fields=["created_at"])

    line_without_sku = order.lines.last()
    line_without_sku.product_sku = None
    line_without_sku.save()

    return order


@pytest.fixture
def payment_for_payload(payment_txn_captured):
    payment_txn_captured.psp_reference = "123"
    payment_txn_captured.save(update_fields=["psp_reference"])
    return payment_txn_captured


@freeze_time()
@mock.patch("saleor.webhook.payloads.generate_order_lines_payload")
@mock.patch("saleor.webhook.payloads.generate_fulfillment_lines_payload")
def test_generate_order_payload(
    mocked_fulfillment_lines,
    mocked_order_lines,
    mocked_fetch_order,
    order_for_payload,
    payment_for_payload,
    customer_user,
):
    fulfillment_lines = '"fulfillment_lines"'
    mocked_fulfillment_lines.return_value = fulfillment_lines
    order_lines = '"order_lines"'
    mocked_order_lines.return_value = order_lines

    order = order_for_payload
    payment = payment_for_payload
    fulfillment = order.fulfillments.first()
    discount_1, discount_2 = list(order.discounts.all())
    shipping_method_channel_listing = order.shipping_method.channel_listings.filter(
        channel=order.channel,
    ).first()

    # when
    payload = json.loads(generate_order_payload(order, customer_user))[0]

    # then
    currency = order.currency

    assert payload == {
        "id": graphene.Node.to_global_id("Order", order.id),
        "type": "Order",
        "token": str(order.id),
        "number": order.number,
        "created": parse_django_datetime(order.created_at),
        "status": order.status,
        "origin": order.origin,
        "user_email": order.user_email,
        "shipping_method_name": order.shipping_method_name,
        "collection_point_name": None,
        "weight": f"{order.weight.value}:{order.weight.unit}",
        "language_code": order.language_code,
        "metadata": order.metadata,
        "private_metadata": order.private_metadata,
        "channel": {
            "id": graphene.Node.to_global_id("Channel", order.channel_id),
            "type": "Channel",
            "slug": order.channel.slug,
            "currency_code": order.channel.currency_code,
        },
        "shipping_method": {
            "id": graphene.Node.to_global_id(
                "ShippingMethod", order.shipping_method_id
            ),
            "name": order.shipping_method.name,
            "type": order.shipping_method.type,
            "currency": shipping_method_channel_listing.currency,
            "price_amount": str(
                quantize_price(
                    shipping_method_channel_listing.price_amount,
                    shipping_method_channel_listing.currency,
                )
            ),
        },
        "payments": [
            {
                "id": graphene.Node.to_global_id("Payment", payment.pk),
                "type": "Payment",
                "gateway": payment.gateway,
                "payment_method_type": payment.payment_method_type,
                "partial": False,
                "cc_brand": payment.cc_brand,
                "is_active": payment.is_active,
                "created": parse_django_datetime(payment.created_at),
                "modified": parse_django_datetime(payment.modified_at),
                "charge_status": payment.charge_status,
                "psp_reference": payment.psp_reference,
                "total": str(quantize_price(payment.total, currency)),
                "captured_amount": str(
                    quantize_price(payment.captured_amount, currency)
                ),
                "currency": payment.currency,
                "billing_email": payment.billing_email,
                "billing_first_name": payment.billing_first_name,
                "billing_last_name": payment.billing_last_name,
                "billing_company_name": payment.billing_company_name,
                "billing_address_1": payment.billing_address_1,
                "billing_address_2": payment.billing_address_2,
                "billing_city": payment.billing_city,
                "billing_city_area": payment.billing_city_area,
                "billing_postal_code": payment.billing_postal_code,
                "billing_country_code": payment.billing_country_code,
                "billing_country_area": payment.billing_country_area,
            }
        ],
        "shipping_address": {
            "id": graphene.Node.to_global_id("Address", order.shipping_address_id),
            "type": "Address",
            "first_name": order.shipping_address.first_name,
            "last_name": order.shipping_address.last_name,
            "company_name": order.shipping_address.company_name,
            "street_address_1": order.shipping_address.street_address_1,
            "street_address_2": order.shipping_address.street_address_2,
            "city": order.shipping_address.city,
            "city_area": order.shipping_address.city_area,
            "postal_code": order.shipping_address.postal_code,
            "country": order.shipping_address.country.code,
            "country_area": order.shipping_address.country_area,
            "phone": str(order.shipping_address.phone),
        },
        "billing_address": {
            "id": graphene.Node.to_global_id("Address", order.billing_address_id),
            "type": "Address",
            "first_name": order.billing_address.first_name,
            "last_name": order.billing_address.last_name,
            "company_name": order.billing_address.company_name,
            "street_address_1": order.billing_address.street_address_1,
            "street_address_2": order.billing_address.street_address_2,
            "city": order.billing_address.city,
            "city_area": order.billing_address.city_area,
            "postal_code": order.billing_address.postal_code,
            "country": order.billing_address.country.code,
            "country_area": order.billing_address.country_area,
            "phone": str(order.billing_address.phone),
        },
        "discounts": [
            {
                "id": graphene.Node.to_global_id("OrderDiscount", discount_1.pk),
                "type": discount_1.type,
                "value_type": discount_1.value_type,
                "value": "20.000",
                "amount_value": str(quantize_price(discount_1.amount_value, currency)),
                "name": discount_1.name,
                "translated_name": discount_1.translated_name,
                "reason": discount_1.reason,
            },
            {
                "id": graphene.Node.to_global_id("OrderDiscount", discount_2.pk),
                "type": discount_2.type,
                "value_type": discount_2.value_type,
                "value": "10.000",
                "amount_value": str(quantize_price(discount_2.amount_value, currency)),
                "name": discount_2.name,
                "translated_name": discount_2.translated_name,
                "reason": discount_2.reason,
            },
        ],
        "original": graphene.Node.to_global_id("Order", order.original_id),
        "lines": json.loads(order_lines),
        "fulfillments": [
            {
                "id": graphene.Node.to_global_id("Fulfillment", fulfillment.pk),
                "type": "Fulfillment",
                "status": fulfillment.status,
                "tracking_number": fulfillment.tracking_number,
                "created": parse_django_datetime(fulfillment.created_at),
                "shipping_refund_amount": "0.00",
                "total_refund_amount": "0.00",
                "lines": json.loads(fulfillment_lines),
            }
        ],
        "collection_point": None,
        "shipping_tax_rate": str(order.shipping_tax_rate),
        "shipping_price_net_amount": str(
            quantize_price(order.shipping_price.net.amount, currency)
        ),
        "shipping_price_gross_amount": str(
            quantize_price(order.shipping_price.gross.amount, currency)
        ),
        "total_net_amount": str(quantize_price(order.total.net.amount, currency)),
        "total_gross_amount": str(quantize_price(order.total.gross.amount, currency)),
        "undiscounted_total_net_amount": str(
            quantize_price(order.undiscounted_total.net.amount, currency)
        ),
        "undiscounted_total_gross_amount": str(
            quantize_price(order.undiscounted_total.gross.amount, currency)
        ),
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
    }

    mocked_fulfillment_lines.assert_called_with(fulfillment)


@freeze_time()
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
@mock.patch("saleor.webhook.payloads._generate_order_lines_payload_for_tax_calculation")
def test_generate_order_payload_for_tax_calculation(
    mocked_order_lines,
    order_for_payload,
    prices_entered_with_tax,
):
    # given
    order = order_for_payload

    tax_configuration = order.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    order_lines = '"order_lines"'
    mocked_order_lines.return_value = order_lines

    order = order_for_payload
    discount_1, discount_2 = list(order.discounts.all())
    user = order.user

    # when
    payload = json.loads(generate_order_payload_for_tax_calculation(order))[0]

    # then
    currency = order.currency

    assert payload == {
        "type": "Order",
        "id": graphene.Node.to_global_id("Order", order.id),
        "channel": {
            "id": graphene.Node.to_global_id("Channel", order.channel_id),
            "type": "Channel",
            "slug": order.channel.slug,
            "currency_code": order.channel.currency_code,
        },
        "address": {
            "id": graphene.Node.to_global_id("Address", order.shipping_address_id),
            "type": "Address",
            "first_name": order.shipping_address.first_name,
            "last_name": order.shipping_address.last_name,
            "company_name": order.shipping_address.company_name,
            "street_address_1": order.shipping_address.street_address_1,
            "street_address_2": order.shipping_address.street_address_2,
            "city": order.shipping_address.city,
            "city_area": order.shipping_address.city_area,
            "postal_code": order.shipping_address.postal_code,
            "country": order.shipping_address.country.code,
            "country_area": order.shipping_address.country_area,
            "phone": str(order.shipping_address.phone),
        },
        "user_id": graphene.Node.to_global_id("User", user.pk),
        "user_public_metadata": user.metadata,
        "included_taxes_in_prices": prices_entered_with_tax,
        "currency": order.currency,
        "shipping_name": order.shipping_method.name,
        "shipping_amount": str(
            quantize_price(order.base_shipping_price_amount, currency)
        ),
        "metadata": order.metadata,
        "discounts": [
            {
                "name": discount_1.name,
                "amount": str(quantize_price(discount_1.amount_value, currency)),
            },
            {
                "name": discount_2.name,
                "amount": str(quantize_price(discount_2.amount_value, currency)),
            },
        ],
        "lines": json.loads(order_lines),
    }
    mocked_order_lines.assert_called_once()


@freeze_time()
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
@mock.patch("saleor.webhook.payloads._generate_order_lines_payload_for_tax_calculation")
def test_generate_order_payload_for_tax_calculation_entire_order_voucher(
    mocked_order_lines, order_for_payload, prices_entered_with_tax, voucher
):
    # given
    order = order_for_payload

    tax_configuration = order.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    order_lines = '"order_lines"'
    mocked_order_lines.return_value = order_lines

    order = order_for_payload
    discount_1, discount_2 = list(order.discounts.all())
    voucher.type = VoucherType.ENTIRE_ORDER
    voucher.apply_once_per_order = False
    voucher.save()
    discount_2.voucher = voucher
    discount_2.save()
    user = order.user

    # when
    payload = json.loads(generate_order_payload_for_tax_calculation(order))[0]

    # then
    currency = order.currency

    assert payload == {
        "type": "Order",
        "id": graphene.Node.to_global_id("Order", order.id),
        "channel": {
            "id": graphene.Node.to_global_id("Channel", order.channel_id),
            "type": "Channel",
            "slug": order.channel.slug,
            "currency_code": order.channel.currency_code,
        },
        "address": {
            "id": graphene.Node.to_global_id("Address", order.shipping_address_id),
            "type": "Address",
            "first_name": order.shipping_address.first_name,
            "last_name": order.shipping_address.last_name,
            "company_name": order.shipping_address.company_name,
            "street_address_1": order.shipping_address.street_address_1,
            "street_address_2": order.shipping_address.street_address_2,
            "city": order.shipping_address.city,
            "city_area": order.shipping_address.city_area,
            "postal_code": order.shipping_address.postal_code,
            "country": order.shipping_address.country.code,
            "country_area": order.shipping_address.country_area,
            "phone": str(order.shipping_address.phone),
        },
        "user_id": graphene.Node.to_global_id("User", user.pk),
        "user_public_metadata": user.metadata,
        "included_taxes_in_prices": prices_entered_with_tax,
        "currency": order.currency,
        "shipping_name": order.shipping_method.name,
        "shipping_amount": str(
            quantize_price(order.base_shipping_price_amount, currency)
        ),
        "metadata": order.metadata,
        "discounts": [
            {
                "name": discount_1.name,
                "amount": str(quantize_price(discount_1.amount_value, currency)),
            },
            {
                "name": discount_2.name,
                "amount": str(quantize_price(discount_2.amount_value, currency)),
            },
        ],
        "lines": json.loads(order_lines),
    }
    mocked_order_lines.assert_called_once()


@freeze_time()
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
@mock.patch("saleor.webhook.payloads._generate_order_lines_payload_for_tax_calculation")
def test_generate_order_payload_for_tax_calculation_line_level_voucher_excluded(
    mocked_order_lines, order_for_payload, prices_entered_with_tax, voucher
):
    # given
    order = order_for_payload

    tax_configuration = order.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])

    order_lines = '"order_lines"'
    mocked_order_lines.return_value = order_lines

    order = order_for_payload
    discount_1, discount_2 = list(order.discounts.all())
    voucher.type = VoucherType.ENTIRE_ORDER
    # line level vouchers should be excluded from discounts
    voucher.apply_once_per_order = True
    voucher.save()
    discount_2.voucher = voucher
    discount_2.save()

    # when
    payload = json.loads(generate_order_payload_for_tax_calculation(order))[0]

    # then
    assert payload["discounts"] == [
        {
            "name": discount_1.name,
            "amount": str(quantize_price(discount_1.amount_value, order.currency)),
        },
    ]
    mocked_order_lines.assert_called_once()


@freeze_time()
@mock.patch("saleor.webhook.payloads.generate_order_lines_payload")
@mock.patch("saleor.webhook.payloads.generate_fulfillment_lines_payload")
def test_generate_order_payload_no_user_email_but_user_set(
    mocked_fulfillment_lines,
    mocked_order_lines,
    fulfilled_order,
    customer_user,
):
    """Test that user email is always set.

    Ensure that the assigned user's email is returned in `user_email` payload field
    when the user_email order value is empty.
    """
    # given
    fulfillment_lines = '"fulfillment_lines"'
    mocked_fulfillment_lines.return_value = fulfillment_lines
    order_lines = '"order_lines"'
    mocked_order_lines.return_value = order_lines

    order = fulfilled_order

    order.user_email = ""
    order.save(update_fields=["user_email"])

    line_without_sku = order.lines.last()
    line_without_sku.product_sku = None
    line_without_sku.save()

    assert order.fulfillments.count() == 1

    # when
    payload = json.loads(generate_order_payload(order, customer_user))[0]

    # then
    assert payload["user_email"] == order.user.email


def test_generate_fulfillment_lines_payload(order_with_lines):
    fulfillment = order_with_lines.fulfillments.create(tracking_number="123")
    line = order_with_lines.lines.first()
    line.sale_id = graphene.Node.to_global_id("Sale", 1)
    line.voucher_code = "code"
    line.save()
    stock = line.allocations.get().stock
    warehouse_pk = stock.warehouse.pk
    fulfillment_line = fulfillment.lines.create(
        order_line=line, quantity=line.quantity, stock=stock
    )
    fulfill_order_lines(
        [OrderLineInfo(line=line, quantity=line.quantity, warehouse_pk=warehouse_pk)],
        get_plugins_manager(allow_replica=False),
    )
    payload = json.loads(generate_fulfillment_lines_payload(fulfillment))[0]

    undiscounted_unit_price_gross = line.undiscounted_unit_price.gross.amount.quantize(
        Decimal("0.01")
    )
    undiscounted_unit_price_net = line.undiscounted_unit_price.net.amount.quantize(
        Decimal("0.01")
    )
    unit_price_gross = line.unit_price.gross.amount.quantize(Decimal("0.01"))
    unit_price_net = line.unit_price.net.amount.quantize(Decimal("0.01"))

    assert payload == {
        "currency": "USD",
        "product_name": line.product_name,
        "variant_name": line.variant_name,
        "product_sku": line.product_sku,
        "product_variant_id": line.product_variant_id,
        "id": graphene.Node.to_global_id("FulfillmentLine", fulfillment_line.id),
        "product_type": "Default Type",
        "quantity": fulfillment_line.quantity,
        "total_price_gross_amount": str(unit_price_gross * fulfillment_line.quantity),
        "total_price_net_amount": str(unit_price_net * fulfillment_line.quantity),
        "type": "FulfillmentLine",
        "undiscounted_unit_price_gross": str(undiscounted_unit_price_gross),
        "undiscounted_unit_price_net": str(undiscounted_unit_price_net),
        "unit_price_gross": str(unit_price_gross),
        "unit_price_net": str(unit_price_net),
        "weight": 0.0,
        "weight_unit": "gram",
        "warehouse_id": graphene.Node.to_global_id(
            "Warehouse", fulfillment_line.stock.warehouse_id
        ),
        "sale_id": line.sale_id,
        "voucher_code": line.voucher_code,
    }


def test_generate_fulfillment_lines_payload_deleted_variant(order_with_lines):
    # given
    fulfillment = order_with_lines.fulfillments.create(tracking_number="123")
    line = order_with_lines.lines.first()
    stock = line.allocations.get().stock
    warehouse_pk = stock.warehouse.pk
    fulfillment.lines.create(order_line=line, quantity=line.quantity, stock=stock)
    fulfill_order_lines(
        [OrderLineInfo(line=line, quantity=line.quantity, warehouse_pk=warehouse_pk)],
        get_plugins_manager(allow_replica=False),
    )

    # when
    line.variant.delete()
    payload = json.loads(generate_fulfillment_lines_payload(fulfillment))[0]

    # then
    assert payload["product_type"] is None
    assert payload["weight"] is None


@freeze_time()
def test_generate_fulfillment_metadata_updated_payload(
    order_with_lines,
    customer_user,
):
    fulfillment = order_with_lines.fulfillments.create(tracking_number="123")

    # when
    payload = json.loads(generate_metadata_updated_payload(fulfillment, customer_user))[
        0
    ]

    # then
    assert payload == {
        "id": graphene.Node.to_global_id("Fulfillment", fulfillment.id),
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
    }


@freeze_time()
def test_generate_gift_card_metadata_updated_payload(
    gift_card,
    customer_user,
):
    # when
    payload = json.loads(generate_metadata_updated_payload(gift_card, customer_user))[0]

    # then
    assert payload == {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.id),
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
    }


@freeze_time()
def test_generate_voucher_metadata_updated_payload(
    voucher,
    customer_user,
):
    # when
    payload = json.loads(generate_metadata_updated_payload(voucher, customer_user))[0]

    # then
    assert payload == {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
    }


def test_order_lines_have_all_required_fields(
    mocked_fetch_order, order, order_line_with_one_allocation
):
    order.lines.add(order_line_with_one_allocation)
    line = order_line_with_one_allocation
    line.voucher_code = "Voucher001"
    line.unit_discount_amount = Decimal("10.0")
    line.unit_discount_type = DiscountValueType.FIXED
    line.undiscounted_unit_price = line.unit_price + line.unit_discount
    line.undiscounted_total_price = line.undiscounted_unit_price * line.quantity
    line.sale_id = graphene.Node.to_global_id("Sale", 1)
    line.save()

    payload = json.loads(generate_order_payload(order))[0]
    lines_payload = payload.get("lines")

    assert len(lines_payload) == 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    line_payload = lines_payload[0]
    unit_net_amount = line.unit_price_net_amount.quantize(Decimal("0.01"))
    unit_gross_amount = line.unit_price_gross_amount.quantize(Decimal("0.01"))
    unit_discount_amount = line.unit_discount_amount.quantize(Decimal("0.01"))
    allocation = line.allocations.first()
    undiscounted_unit_price_net_amount = (
        line.undiscounted_unit_price.net.amount.quantize(Decimal("0.01"))
    )
    undiscounted_unit_price_gross_amount = (
        line.undiscounted_unit_price.gross.amount.quantize(Decimal("0.01"))
    )
    undiscounted_total_price_net_amount = (
        line.undiscounted_total_price.net.amount.quantize(Decimal("0.01"))
    )
    undiscounted_total_price_gross_amount = (
        line.undiscounted_total_price.gross.amount.quantize(Decimal("0.01"))
    )

    total_line = line.total_price
    global_warehouse_id = graphene.Node.to_global_id(
        "Warehouse", allocation.stock.warehouse_id
    )
    assert line_payload == {
        "id": line_id,
        "type": "OrderLine",
        "product_name": line.product_name,
        "variant_name": line.variant_name,
        "translated_product_name": line.translated_product_name,
        "translated_variant_name": line.translated_variant_name,
        "product_sku": line.product_sku,
        "product_variant_id": line.product_variant_id,
        "quantity": line.quantity,
        "currency": line.currency,
        "unit_discount_amount": str(unit_discount_amount),
        "unit_discount_type": line.unit_discount_type,
        "unit_discount_reason": line.unit_discount_reason,
        "unit_price_net_amount": str(unit_net_amount),
        "unit_price_gross_amount": str(unit_gross_amount),
        "total_price_net_amount": str(total_line.net.amount.quantize(Decimal("0.01"))),
        "total_price_gross_amount": str(
            total_line.gross.amount.quantize(Decimal("0.01"))
        ),
        "tax_rate": str(line.tax_rate.quantize(Decimal("0.0001"))),
        "allocations": [
            {
                "warehouse_id": global_warehouse_id,
                "quantity_allocated": allocation.quantity_allocated,
            }
        ],
        "undiscounted_unit_price_net_amount": str(undiscounted_unit_price_net_amount),
        "undiscounted_unit_price_gross_amount": str(
            undiscounted_unit_price_gross_amount
        ),
        "undiscounted_total_price_net_amount": str(undiscounted_total_price_net_amount),
        "undiscounted_total_price_gross_amount": str(
            undiscounted_total_price_gross_amount
        ),
        "voucher_code": line.voucher_code,
        "sale_id": line.sale_id,
    }


@pytest.mark.parametrize(
    ("charge_taxes", "prices_entered_with_tax"),
    [(False, False), (False, True), (True, False), (True, True)],
)
def test_order_lines_for_tax_calculation_have_all_required_fields(
    order,
    order_line_with_one_allocation,
    charge_taxes,
    prices_entered_with_tax,
):
    tax_configuration = order.channel.tax_configuration
    tax_configuration.charge_taxes = charge_taxes
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    order.lines.add(order_line_with_one_allocation)
    currency = order.currency
    line = order_line_with_one_allocation
    line.voucher_code = "Voucher001"
    line.unit_discount_amount = Decimal("10.0")
    line.unit_discount_type = DiscountValueType.FIXED
    line.undiscounted_unit_price = line.unit_price + line.unit_discount
    line.undiscounted_total_price = line.undiscounted_unit_price * line.quantity
    line.sale_id = graphene.Node.to_global_id("Sale", 1)
    line.save()
    variant = line.variant
    product = variant.product
    product_type = product.product_type
    product.metadata = {"product_meta": "value"}
    product.save()
    product_type.metadata = {"product_type_meta": "value"}
    product_type.save()

    payload = json.loads(generate_order_payload_for_tax_calculation(order))[0]
    lines_payload = payload.get("lines")

    assert len(lines_payload) == 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    line_payload = lines_payload[0]
    assert line_payload == {
        "type": "OrderLine",
        "id": line_id,
        "variant_id": graphene.Node.to_global_id("ProductVariant", variant.id),
        "full_name": variant.display_product(),
        "product_name": line.product_name,
        "variant_name": line.variant_name,
        "product_metadata": {"product_meta": "value"},
        "product_type_metadata": {"product_type_meta": "value"},
        "quantity": line.quantity,
        "sku": line.product_sku,
        "charge_taxes": charge_taxes,
        "unit_amount": str(quantize_price(line.base_unit_price_amount, currency)),
        "total_amount": str(
            quantize_price(line.base_unit_price_amount * line.quantity, currency)
        ),
    }


@pytest.mark.parametrize("charge_taxes", [True, False])
def test_order_lines_for_tax_calculation_with_removed_variant(
    order, order_line_with_one_allocation, charge_taxes
):
    tax_configuration = order.channel.tax_configuration
    tax_configuration.charge_taxes = charge_taxes
    tax_configuration.save(update_fields=["charge_taxes"])
    tax_configuration.country_exceptions.all().delete()

    order.lines.add(order_line_with_one_allocation)
    currency = order.currency
    line = order_line_with_one_allocation
    line.voucher_code = "Voucher001"
    line.unit_discount_amount = Decimal("10.0")
    line.unit_discount_type = DiscountValueType.FIXED
    line.undiscounted_unit_price = line.unit_price + line.unit_discount
    line.undiscounted_total_price = line.undiscounted_unit_price * line.quantity
    line.sale_id = graphene.Node.to_global_id("Sale", 1)
    variant = line.variant
    line.variant = None
    line.save()

    payload = json.loads(generate_order_payload_for_tax_calculation(order))[0]
    lines_payload = payload.get("lines")

    assert len(lines_payload) == 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    line_payload = lines_payload[0]
    assert line_payload == {
        "type": "OrderLine",
        "id": line_id,
        "variant_id": graphene.Node.to_global_id("ProductVariant", variant.id),
        "full_name": None,
        "product_name": line.product_name,
        "variant_name": line.variant_name,
        "product_metadata": {},
        "product_type_metadata": {},
        "quantity": line.quantity,
        "sku": line.product_sku,
        "charge_taxes": charge_taxes,
        "unit_amount": str(quantize_price(line.base_unit_price_amount, currency)),
        "total_amount": str(
            quantize_price(line.base_unit_price_amount * line.quantity, currency)
        ),
    }


def test_order_line_without_sku_still_has_id(order, order_line_with_one_allocation):
    order.lines.add(order_line_with_one_allocation)
    line = order_line_with_one_allocation
    line.unit_discount_amount = Decimal("10.0")
    line.unit_discount_type = DiscountValueType.FIXED
    line.undiscounted_unit_price = line.unit_price + line.unit_discount
    line.undiscounted_total_price = line.undiscounted_unit_price * line.quantity
    line.product_sku = None
    line.save()

    payload = json.loads(generate_order_payload(order))[0]
    lines_payload = payload.get("lines")

    assert len(lines_payload) == 1

    line_payload = lines_payload[0]
    assert line_payload["product_sku"] is None
    assert line_payload["product_variant_id"] == line.product_variant_id


@freeze_time()
def test_generate_order_metadata_updated_payload(
    order_for_payload,
    customer_user,
):
    order = order_for_payload

    # when
    payload = json.loads(generate_metadata_updated_payload(order, customer_user))[0]

    # then
    assert payload == {
        "id": graphene.Node.to_global_id("Order", order.id),
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
    }


def test_generate_collection_payload(collection):
    payload = json.loads(generate_collection_payload(collection))
    expected_payload = [
        {
            "type": "Collection",
            "id": graphene.Node.to_global_id("Collection", collection.id),
            "name": collection.name,
            "description": collection.description,
            "background_image": None,
            "background_image_alt": "",
            "private_metadata": {},
            "metadata": {},
            "meta": {
                "issued_at": ANY,
                "version": __version__,
                "issuing_principal": {"id": None, "type": None},
            },
        }
    ]

    assert payload == expected_payload


@pytest.mark.parametrize("tax_rate", [0, 23])
def test_generate_product_payload_charge_taxes(
    product_with_two_variants, default_tax_class, tax_rate
):
    # given
    product = product_with_two_variants
    default_tax_class.country_rates.all().delete()
    default_tax_class.country_rates.create(country="PL", rate=tax_rate)
    product.tax_class = default_tax_class
    product.save(update_fields=["tax_class"])

    # when
    payload = json.loads(generate_product_payload(product_with_two_variants))

    # then
    expected_charge_taxes = tax_rate != 0
    assert payload[0]["charge_taxes"] == expected_charge_taxes


@freeze_time()
def test_generate_shipping_zone_metadata_updated_payload(
    shipping_zone,
    customer_user,
):
    # when
    payload = json.loads(
        generate_metadata_updated_payload(shipping_zone, customer_user)
    )[0]

    # then
    assert payload == {
        "id": graphene.Node.to_global_id("ShippingZone", shipping_zone.id),
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
    }


@freeze_time()
def test_generate_collection_metadata_updated_payload(
    collection,
    customer_user,
):
    # when
    payload = json.loads(generate_metadata_updated_payload(collection, customer_user))[
        0
    ]

    # then
    assert payload == {
        "id": graphene.Node.to_global_id("Collection", collection.id),
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
    }


def test_generate_base_product_variant_payload(product_with_two_variants):
    stocks_to_serialize = [
        variant.stocks.first() for variant in product_with_two_variants.variants.all()
    ]
    first_stock, second_stock = stocks_to_serialize
    payload = json.loads(
        generate_product_variant_with_stock_payload(stocks_to_serialize)
    )
    expected_payload = [
        {
            "type": "Stock",
            "id": graphene.Node.to_global_id("Stock", first_stock.id),
            "product_id": graphene.Node.to_global_id(
                "Product", first_stock.product_variant.product_id
            ),
            "product_variant_id": graphene.Node.to_global_id(
                "ProductVariant", first_stock.product_variant_id
            ),
            "warehouse_id": graphene.Node.to_global_id(
                "Warehouse", first_stock.warehouse_id
            ),
            "product_slug": "test-product-with-two-variant",
            "meta": {
                "issuing_principal": {"id": None, "type": None},
                "issued_at": ANY,
                "version": __version__,
            },
        },
        {
            "type": "Stock",
            "id": graphene.Node.to_global_id("Stock", second_stock.id),
            "product_id": graphene.Node.to_global_id(
                "Product", second_stock.product_variant.product_id
            ),
            "product_variant_id": graphene.Node.to_global_id(
                "ProductVariant", second_stock.product_variant_id
            ),
            "warehouse_id": graphene.Node.to_global_id(
                "Warehouse", second_stock.warehouse_id
            ),
            "product_slug": "test-product-with-two-variant",
            "meta": {
                "issuing_principal": {"id": None, "type": None},
                "issued_at": ANY,
                "version": __version__,
            },
        },
    ]
    assert payload == expected_payload


@freeze_time()
def test_generate_product_metadata_updated_payload(
    product_with_variant_with_two_attributes,
    customer_user,
):
    product = product_with_variant_with_two_attributes

    # when
    payload = json.loads(generate_metadata_updated_payload(product, customer_user))[0]

    # then
    assert payload == {
        "id": graphene.Node.to_global_id("Product", product.id),
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
    }


def test_generate_product_variant_payload(
    product_with_variant_with_two_attributes,
    product_with_images,
    channel_USD,
    staff_user,
):
    variant = product_with_variant_with_two_attributes.variants.first()
    payload = json.loads(generate_product_variant_payload([variant], staff_user))[0]
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    additional_fields = ["channel_listings"]
    extra_dict_data = ["attributes", "product_id", "media", "meta"]
    payload_fields = list(
        chain(
            ["id", "type"], PRODUCT_VARIANT_FIELDS, extra_dict_data, additional_fields
        )
    )

    for field in payload_fields:
        assert payload.get(field) is not None

    assert variant_id is not None
    assert payload["id"] == variant_id
    assert payload["sku"] == "prodVar1"
    assert len(payload["attributes"]) == 2
    assert len(payload["channel_listings"]) == 1
    assert payload["channel_listings"][0] == {
        "cost_price_amount": "1.000",
        "currency": "USD",
        "id": ANY,
        "channel_slug": channel_USD.slug,
        "price_amount": "10.000",
        "type": "ProductVariantChannelListing",
    }
    assert payload["meta"] == {
        "issuing_principal": generate_requestor(staff_user),
        "issued_at": ANY,
        "version": __version__,
    }
    assert len(payload.keys()) == len(payload_fields)


def test_generate_product_variant_with_external_media_payload(
    product_with_variant_with_external_media, channel_USD
):
    variant = product_with_variant_with_external_media.variants.first()
    payload = json.loads(generate_product_variant_payload([variant]))[0]
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    additional_fields = ["channel_listings"]
    extra_dict_data = ["attributes", "product_id", "media", "meta"]
    payload_fields = list(
        chain(
            ["id", "type"], PRODUCT_VARIANT_FIELDS, extra_dict_data, additional_fields
        )
    )
    for field in payload_fields:
        assert payload.get(field) is not None

    assert variant_id is not None
    assert payload["id"] == variant_id
    assert payload["sku"] == "prodVar1"
    assert payload["media"] == [
        {"alt": "video_1", "url": "https://www.youtube.com/watch?v=di8_dJ3Clyo"}
    ]
    assert len(payload["attributes"]) == 2
    assert len(payload["channel_listings"]) == 1
    assert payload["channel_listings"][0] == {
        "cost_price_amount": "1.000",
        "currency": "USD",
        "id": ANY,
        "price_amount": "10.000",
        "channel_slug": channel_USD.slug,
        "type": "ProductVariantChannelListing",
    }
    assert len(payload.keys()) == len(payload_fields)


def test_generate_product_variant_without_sku_payload(
    product_with_variant_with_two_attributes, product_with_images, channel_USD
):
    variant = product_with_variant_with_two_attributes.variants.first()
    variant.sku = None
    variant.save()
    payload = json.loads(generate_product_variant_payload([variant]))[0]
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    additional_fields = ["channel_listings"]
    extra_dict_data = ["attributes", "product_id", "media", "meta"]
    payload_fields = list(
        chain(
            ["id", "type"], PRODUCT_VARIANT_FIELDS, extra_dict_data, additional_fields
        )
    )
    assert variant_id is not None
    assert payload["id"] == variant_id
    assert payload["sku"] is None
    assert len(payload["attributes"]) == 2
    assert len(payload["channel_listings"]) == 1
    assert payload["channel_listings"][0] == {
        "cost_price_amount": "1.000",
        "currency": "USD",
        "id": ANY,
        "channel_slug": channel_USD.slug,
        "price_amount": "10.000",
        "type": "ProductVariantChannelListing",
    }
    assert len(payload.keys()) == len(payload_fields)


def test_generate_product_variant_deleted_payload(
    product_with_variant_with_two_attributes,
):
    variant = product_with_variant_with_two_attributes.variants.prefetch_related(
        "channel_listings",
        "attributes__values",
        "variant_media",
    ).first()
    ProductVariant.objects.filter(id=variant.id).delete()
    payload = json.loads(generate_product_variant_payload([variant]))[0]
    [_, payload_variant_id] = graphene.Node.from_global_id(payload["id"])
    additional_fields = ["channel_listings"]
    extra_dict_data = ["attributes", "product_id", "media", "meta"]
    payload_fields = list(
        chain(
            ["id", "type"], PRODUCT_VARIANT_FIELDS, extra_dict_data, additional_fields
        )
    )
    for field in payload_fields:
        assert payload.get(field) is not None

    assert payload_variant_id != "None"
    assert payload["id"] == variant.get_global_id()
    assert payload["sku"] == "prodVar1"
    assert len(payload["attributes"]) == 2
    assert len(payload["channel_listings"]) == 1
    assert len(payload.keys()) == len(payload_fields)


@freeze_time()
def test_generate_product_variant_metadata_updated_payload(
    product_with_variant_with_two_attributes,
    customer_user,
):
    variant = product_with_variant_with_two_attributes.variants.first()

    # when
    payload = json.loads(generate_metadata_updated_payload(variant, customer_user))[0]

    # then
    assert payload == {
        "id": graphene.Node.to_global_id("ProductVariant", variant.id),
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
    }


def test_generate_invoice_payload(fulfilled_order):
    fulfilled_order.origin = OrderOrigin.CHECKOUT
    fulfilled_order.save(update_fields=["origin"])
    invoice = fulfilled_order.invoices.first()
    payload = json.loads(generate_invoice_payload(invoice))[0]
    undiscounted_total_net = fulfilled_order.undiscounted_total_net_amount.quantize(
        Decimal("0.01")
    )
    undiscounted_total_gross = fulfilled_order.undiscounted_total_gross_amount.quantize(
        Decimal("0.01")
    )

    del payload["meta"]["issued_at"]
    assert payload == {
        "type": "Invoice",
        "id": graphene.Node.to_global_id("Invoice", invoice.id),
        "meta": {
            "issuing_principal": {"id": None, "type": None},
            "version": __version__,
        },
        "order": {
            "type": "Order",
            "token": str(invoice.order.id),
            "id": graphene.Node.to_global_id("Order", invoice.order.id),
            "language_code": "en",
            "private_metadata": invoice.order.private_metadata,
            "metadata": invoice.order.metadata,
            "created": ANY,
            "status": "fulfilled",
            "origin": OrderOrigin.CHECKOUT,
            "user_email": "test@example.com",
            "shipping_method_name": "DHL",
            "collection_point_name": None,
            "shipping_price_net_amount": "10.00",
            "shipping_price_gross_amount": "12.30",
            "shipping_tax_rate": "0.2300",
            "total_net_amount": "80.00",
            "total_gross_amount": "98.40",
            "weight": "0.0:g",
            "undiscounted_total_net_amount": str(undiscounted_total_net),
            "undiscounted_total_gross_amount": str(undiscounted_total_gross),
        },
        "number": "01/12/2020/TEST",
        "created": ANY,
        "external_url": "http://www.example.com/invoice.pdf",
    }


def test_generate_list_gateways_payload(checkout):
    currency = "USD"
    payload = generate_list_gateways_payload(currency, checkout)
    data = json.loads(payload)
    expected_data = json.loads(generate_checkout_payload(checkout))[0]
    del data["checkout"]["meta"]["issued_at"], expected_data["meta"]["issued_at"]
    assert data["checkout"] == expected_data
    assert data["checkout"]["channel"]["id"] == graphene.Node.to_global_id(
        "Channel", checkout.channel.pk
    )
    assert data["currency"] == currency


def test_generate_payment_payload(dummy_webhook_app_payment_data, order_line):
    payload = generate_payment_payload(dummy_webhook_app_payment_data)
    expected_payload = asdict(dummy_webhook_app_payment_data)

    expected_payload["amount"] = Decimal(expected_payload["amount"]).quantize(
        Decimal("0.01")
    )
    expected_payload["payment_method"] = from_payment_app_id(
        dummy_webhook_app_payment_data.gateway
    ).name
    expected_payload["meta"] = generate_meta(requestor_data=generate_requestor())
    payload = json.loads(payload)
    expected_payload = json.loads(json.dumps(expected_payload, cls=CustomJsonEncoder))

    del payload["meta"]["issued_at"], expected_payload["meta"]["issued_at"]
    assert payload == expected_payload


def test_generate_payment_payload_with_refund_data(
    dummy_webhook_app_payment_data, order_with_lines
):
    # given
    refund_data = RefundData(
        order_lines_to_refund=[
            OrderLineInfo(line=line, quantity=line.quantity, variant=line.variant)
            for line in order_with_lines.lines.all()
        ]
    )
    dummy_webhook_app_payment_data.refund_data = refund_data

    # when
    payload = generate_payment_payload(dummy_webhook_app_payment_data)
    expected_payload = asdict(dummy_webhook_app_payment_data)
    expected_payload["amount"] = Decimal(expected_payload["amount"]).quantize(
        Decimal("0.01")
    )
    expected_payload["payment_method"] = from_payment_app_id(
        dummy_webhook_app_payment_data.gateway
    ).name
    expected_payload["meta"] = generate_meta(requestor_data=generate_requestor())
    expected_payload["refund_data"] = _generate_refund_data_payload(asdict(refund_data))
    payload = json.loads(payload)
    expected_payload = json.loads(json.dumps(expected_payload, cls=CustomJsonEncoder))

    # then
    del payload["meta"]["issued_at"], expected_payload["meta"]["issued_at"]
    assert payload == expected_payload


def test_generate_payment_payload_fulfillment_return(
    dummy_webhook_app_payment_data, fulfillment
):
    refund_data = RefundData(
        fulfillment_lines_to_refund=[
            FulfillmentLineData(line=line, quantity=line.quantity)
            for line in fulfillment.lines.all()
        ]
    )
    dummy_webhook_app_payment_data.refund_data = refund_data
    payload = generate_payment_payload(dummy_webhook_app_payment_data)
    expected_payload = asdict(dummy_webhook_app_payment_data)

    expected_payload["refund_data"] = _generate_refund_data_payload(asdict(refund_data))

    expected_payload["amount"] = Decimal(expected_payload["amount"]).quantize(
        Decimal("0.01")
    )
    expected_payload["payment_method"] = from_payment_app_id(
        dummy_webhook_app_payment_data.gateway
    ).name
    expected_payload["meta"] = generate_meta(requestor_data=generate_requestor())
    payload = json.loads(payload)
    expected_payload = json.loads(json.dumps(expected_payload, cls=CustomJsonEncoder))

    del payload["meta"]["issued_at"], expected_payload["meta"]["issued_at"]
    assert payload == expected_payload


def test_generate_payment_with_transactions_payload(dummy_webhook_app_payment_data):
    transaction_data = {
        "token": "token",
        "is_success": True,
        "kind": "auth",
        "gateway_response": {"status": "SUCCESS"},
        "amount": {
            "amount": str(
                quantize_price(
                    dummy_webhook_app_payment_data.amount,
                    dummy_webhook_app_payment_data.currency,
                )
            ),
            "currency": dummy_webhook_app_payment_data.currency,
        },
    }

    dummy_webhook_app_payment_data.transactions = [TransactionData(**transaction_data)]

    payload = generate_payment_payload(dummy_webhook_app_payment_data)
    expected_payload = asdict(dummy_webhook_app_payment_data)

    expected_payload["amount"] = Decimal(expected_payload["amount"]).quantize(
        Decimal("0.01")
    )
    expected_payload["payment_method"] = from_payment_app_id(
        dummy_webhook_app_payment_data.gateway
    ).name

    expected_payload["meta"] = generate_meta(requestor_data=generate_requestor())
    payload = json.loads(payload)
    expected_payload = json.loads(json.dumps(expected_payload, cls=CustomJsonEncoder))

    assert expected_payload["transactions"]
    del payload["meta"]["issued_at"], expected_payload["meta"]["issued_at"]
    assert payload == expected_payload


def test_generate_transaction_item_metadata_updated_payload(
    transaction_item_created_by_user, customer_user
):
    # when
    payload = json.loads(
        generate_metadata_updated_payload(
            transaction_item_created_by_user, customer_user
        )
    )[0]

    # then
    expected_payload = {
        "id": graphene.Node.to_global_id(
            "TransactionItem", transaction_item_created_by_user.token
        ),
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
    }
    del payload["meta"]["issued_at"], expected_payload["meta"]["issued_at"]
    assert payload == expected_payload


def test_generate_checkout_lines_payload(checkout_with_single_item):
    payload = json.loads(generate_checkout_payload(checkout_with_single_item))[0]
    assert payload.get("lines")

    variant = checkout_with_single_item.lines.first().variant
    line = payload["lines"][0]
    assert line["sku"] == variant.sku
    assert line["variant_id"] == variant.get_global_id()


def test_generate_checkout_lines_payload_when_variant_without_listing(
    checkout_with_single_item,
):
    line_without_listing = checkout_with_single_item.lines.first()
    line_without_listing.variant.channel_listings.all().delete()
    payload = json.loads(generate_checkout_payload(checkout_with_single_item))[0]
    assert payload.get("lines")

    variant = checkout_with_single_item.lines.first().variant
    line = payload["lines"][0]
    assert line["sku"] == variant.sku
    assert line["variant_id"] == variant.get_global_id()
    assert (
        Decimal(line["base_price"])
        == line_without_listing.undiscounted_unit_price.amount
    )


def test_generate_checkout_lines_payload_custom_price(checkout_with_single_item):
    line = checkout_with_single_item.lines.first()
    price_override = Decimal("11.11")
    line.price_override = price_override
    line.save(update_fields=["price_override"])

    payload = json.loads(generate_checkout_payload(checkout_with_single_item))[0]
    assert payload.get("lines")

    variant = line.variant

    line_data = payload["lines"][0]
    assert line_data["sku"] == variant.sku
    assert line_data["variant_id"] == variant.get_global_id()
    assert line_data["base_price"] == str(price_override)


@freeze_time()
def test_generate_checkout_metadata_updated_payload(
    checkout_with_single_item,
    customer_user,
):
    checkout = checkout_with_single_item

    # when
    payload = json.loads(generate_metadata_updated_payload(checkout, customer_user))[0]

    # then
    assert payload == {
        "id": graphene.Node.to_global_id("Checkout", checkout.token),
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
    }


def test_generate_product_translation_payload(product_translation_fr):
    payload = generate_translation_payload(product_translation_fr)
    data = json.loads(payload)
    assert data["id"] == graphene.Node.to_global_id(
        "Product", product_translation_fr.product_id
    )
    assert data["language_code"] == product_translation_fr.language_code
    assert "product_id" not in data.keys()
    assert "product_variant_id" not in data.keys()
    assert "attribute_id" not in data.keys()
    assert "page_id" not in data.keys()

    translation_keys = {i["key"]: i["value"] for i in data["keys"]}
    assert translation_keys["name"] == product_translation_fr.name
    assert translation_keys["description"] == product_translation_fr.description


def test_generate_product_variant_translation_payload(variant_translation_fr):
    payload = generate_translation_payload(variant_translation_fr)
    data = json.loads(payload)
    assert data["id"] == graphene.Node.to_global_id(
        "ProductVariant", variant_translation_fr.product_variant_id
    )
    assert data["language_code"] == variant_translation_fr.language_code
    assert "product_id" not in data.keys()
    assert "product_variant_id" not in data.keys()
    assert "attribute_id" not in data.keys()
    assert "page_id" not in data.keys()

    translation_keys = {i["key"]: i["value"] for i in data["keys"]}
    assert translation_keys["name"] == variant_translation_fr.name


def test_generate_choices_attribute_value_translation_payload(
    translated_attribute_value, color_attribute
):
    payload = generate_translation_payload(translated_attribute_value)
    data = json.loads(payload)
    assert data["id"] == graphene.Node.to_global_id(
        "AttributeValue", translated_attribute_value.attribute_value_id
    )
    assert data["language_code"] == translated_attribute_value.language_code
    assert data["product_id"] is None
    assert data["product_variant_id"] is None
    assert data["attribute_id"] == graphene.Node.to_global_id(
        "Attribute", color_attribute.id
    )
    assert data["page_id"] is None

    translation_keys = {i["key"]: i["value"] for i in data["keys"]}
    assert translation_keys["name"] == translated_attribute_value.name


def test_generate_unique_product_attribute_value_translation_payload(
    translated_product_unique_attribute_value, product, rich_text_attribute
):
    translated_attribute_value = translated_product_unique_attribute_value
    payload = generate_translation_payload(translated_attribute_value)
    data = json.loads(payload)
    assert data["id"] == graphene.Node.to_global_id(
        "AttributeValue", translated_attribute_value.attribute_value_id
    )
    assert data["language_code"] == translated_attribute_value.language_code
    assert data["product_id"] == graphene.Node.to_global_id("Product", product.id)
    assert data["product_variant_id"] is None
    assert data["attribute_id"] == graphene.Node.to_global_id(
        "Attribute", rich_text_attribute.id
    )
    assert data["page_id"] is None
    assert data["page_type_id"] is None
    translation_keys = {i["key"]: i["value"] for i in data["keys"]}
    assert translation_keys["rich_text"] == translated_attribute_value.rich_text


def test_generate_unique_variant_attribute_value_translation_payload(
    translated_variant_unique_attribute_value, variant, rich_text_attribute
):
    translated_attribute_value = translated_variant_unique_attribute_value
    payload = generate_translation_payload(translated_attribute_value)
    data = json.loads(payload)
    assert data["id"] == graphene.Node.to_global_id(
        "AttributeValue", translated_attribute_value.attribute_value_id
    )
    assert data["language_code"] == translated_attribute_value.language_code
    assert data["product_id"] == graphene.Node.to_global_id(
        "Product", variant.product_id
    )
    assert data["product_variant_id"] == graphene.Node.to_global_id(
        "ProductVariant", variant.id
    )
    assert data["attribute_id"] == graphene.Node.to_global_id(
        "Attribute", rich_text_attribute.id
    )
    assert data["page_id"] is None
    assert data["page_type_id"] is None
    translation_keys = {i["key"]: i["value"] for i in data["keys"]}
    assert translation_keys["rich_text"] == translated_attribute_value.rich_text


def test_generate_unique_page_attribute_value_translation_payload(
    translated_page_unique_attribute_value,
    page,
    rich_text_attribute_page_type,
):
    translated_attribute_value = translated_page_unique_attribute_value
    payload = generate_translation_payload(translated_attribute_value)
    data = json.loads(payload)
    assert data["id"] == graphene.Node.to_global_id(
        "AttributeValue", translated_attribute_value.attribute_value_id
    )
    assert data["language_code"] == translated_attribute_value.language_code
    assert data["product_id"] is None
    assert data["product_variant_id"] is None
    assert data["attribute_id"] == graphene.Node.to_global_id(
        "Attribute", rich_text_attribute_page_type.id
    )
    assert data["page_id"] == graphene.Node.to_global_id("Page", page.id)
    assert data["page_type_id"] == graphene.Node.to_global_id(
        "PageType", page.page_type_id
    )
    translation_keys = {i["key"]: i["value"] for i in data["keys"]}
    assert translation_keys["rich_text"] == translated_attribute_value.rich_text


def test_generate_customer_payload(customer_user, address_other_country, address):
    customer = customer_user
    customer.default_billing_address = address_other_country
    customer.save()
    payload = json.loads(generate_customer_payload(customer))[0]

    expected_payload = {
        "type": "User",
        "id": graphene.Node.to_global_id("User", customer.id),
        "meta": {
            "issuing_principal": {"id": None, "type": None},
            "version": __version__,
        },
        "default_shipping_address": {
            "type": "Address",
            "id": graphene.Node.to_global_id(
                "Address", customer.default_shipping_address_id
            ),
            "first_name": customer.default_shipping_address.first_name,
            "last_name": customer.default_shipping_address.last_name,
            "company_name": customer.default_shipping_address.company_name,
            "street_address_1": customer.default_shipping_address.street_address_1,
            "street_address_2": customer.default_shipping_address.street_address_2,
            "city": customer.default_shipping_address.city,
            "city_area": customer.default_shipping_address.city_area,
            "postal_code": customer.default_shipping_address.postal_code,
            "country": customer.default_shipping_address.country,
            "country_area": customer.default_shipping_address.country_area,
            "phone": customer.default_shipping_address.phone,
        },
        "default_billing_address": {
            "type": "Address",
            "id": graphene.Node.to_global_id(
                "Address", customer.default_billing_address_id
            ),
            "first_name": customer.default_billing_address.first_name,
            "last_name": customer.default_billing_address.last_name,
            "company_name": customer.default_billing_address.company_name,
            "street_address_1": customer.default_billing_address.street_address_1,
            "street_address_2": customer.default_billing_address.street_address_2,
            "city": customer.default_billing_address.city,
            "city_area": customer.default_billing_address.city_area,
            "postal_code": customer.default_billing_address.postal_code,
            "country": customer.default_billing_address.country,
            "country_area": customer.default_billing_address.country_area,
            "phone": customer.default_billing_address.phone,
        },
        "addresses": [
            {
                "type": "Address",
                "id": graphene.Node.to_global_id(
                    "Address", customer.default_shipping_address_id
                ),
                "first_name": customer.default_shipping_address.first_name,
                "last_name": customer.default_shipping_address.last_name,
                "company_name": customer.default_shipping_address.company_name,
                "street_address_1": customer.default_shipping_address.street_address_1,
                "street_address_2": customer.default_shipping_address.street_address_2,
                "city": customer.default_shipping_address.city,
                "city_area": customer.default_shipping_address.city_area,
                "postal_code": customer.default_shipping_address.postal_code,
                "country": customer.default_shipping_address.country,
                "country_area": customer.default_shipping_address.country_area,
                "phone": customer.default_shipping_address.phone,
            }
        ],
        "language_code": customer.language_code,
        "private_metadata": customer.private_metadata,
        "metadata": customer.metadata,
        "email": customer.email,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "is_active": customer.is_active,
        "date_joined": ANY,
    }
    del payload["meta"]["issued_at"]

    assert payload == expected_payload


@freeze_time()
def test_generate_customer_metadata_updated_payload(
    customer_user,
):
    # when
    payload = json.loads(
        generate_metadata_updated_payload(customer_user, customer_user)
    )[0]

    # then
    assert payload == {
        "id": graphene.Node.to_global_id("User", customer_user.id),
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
    }


def test_generate_collection_point_payload(order_with_lines_for_cc):
    payload = json.loads(generate_order_payload(order_with_lines_for_cc))[0]

    payload_collection_point = payload.get("collection_point")

    assert payload_collection_point
    assert payload_collection_point.get("address")
    assert payload_collection_point.get("email") == "local@example.com"
    assert payload_collection_point.get("name") == "Local Warehouse"
    assert not payload_collection_point.get("is_private")
    assert (
        payload_collection_point.get("click_and_collect_option")
        == WarehouseClickAndCollectOption.LOCAL_STOCK
    )


def test_generate_sale_payload_no_previous_and_current_has_empty_catalogue_lists(
    promotion_converted_from_sale,
):
    promotion = promotion_converted_from_sale
    payload = json.loads(generate_sale_payload(promotion))[0]

    assert not payload["categories_added"]
    assert not payload["categories_removed"]
    assert not payload["collections_added"]
    assert not payload["collections_removed"]
    assert not payload["products_added"]
    assert not payload["products_removed"]

    assert graphene.Node.to_global_id("Sale", promotion.old_sale_id) == payload["id"]


def test_generate_sale_payload_with_current_only_has_empty_removed_fields(
    promotion_converted_from_sale,
):
    catalogue_info = {
        "categories": {1, 2, 3},
        "collections": {45, 70, 90},
        "products": {4, 5, 6},
        "variants": {"aa", "bb", "cc"},
    }
    promotion = promotion_converted_from_sale
    payload = json.loads(
        generate_sale_payload(promotion, current_catalogue=catalogue_info)
    )[0]

    assert set(payload["categories_added"]) == catalogue_info["categories"]
    assert set(payload["collections_added"]) == catalogue_info["collections"]
    assert set(payload["products_added"]) == catalogue_info["products"]
    assert set(payload["variants_added"]) == catalogue_info["variants"]
    assert not payload["categories_removed"]
    assert not payload["collections_removed"]
    assert not payload["products_removed"]
    assert not payload["variants_removed"]


def test_generate_sale_payload_with_current_only_has_empty_added_fields(
    promotion_converted_from_sale,
):
    promotion = promotion_converted_from_sale
    catalogue_info = {
        "categories": {1, 2, 3},
        "collections": {45, 70, 90},
        "products": {4, 5, 6},
        "variants": {"aa", "bb", "cc"},
    }
    payload = json.loads(
        generate_sale_payload(promotion, previous_catalogue=catalogue_info)
    )[0]

    assert set(payload["categories_removed"]) == catalogue_info["categories"]
    assert set(payload["collections_removed"]) == catalogue_info["collections"]
    assert set(payload["products_removed"]) == catalogue_info["products"]
    assert set(payload["variants_removed"]) == catalogue_info["variants"]
    assert not payload["categories_added"]
    assert not payload["collections_added"]
    assert not payload["products_added"]
    assert not payload["variants_added"]


def test_generate_sale_payload_calculates_set_differences(
    promotion_converted_from_sale,
):
    promotion = promotion_converted_from_sale
    previous_info = {
        "categories": {1, 2, 3},
        "collections": {45, 70, 90},
        "products": {4, 5, 6},
        "variants": {"aaa", "bbb", "ccc"},
    }
    current_info = {
        "categories": {4, 2, 3},
        "collections": set(),
        "products": {4, 5, 6, 10, 20},
        "variants": {"aaa", "bbb", "ddd"},
    }

    payload = json.loads(
        generate_sale_payload(
            promotion, previous_catalogue=previous_info, current_catalogue=current_info
        )
    )[0]

    assert set(payload["categories_removed"]) == {1}
    assert set(payload["categories_added"]) == {4}
    assert set(payload["collections_removed"]) == {45, 70, 90}
    assert not payload["collections_added"]
    assert not payload["products_removed"]
    assert set(payload["products_added"]) == {10, 20}
    assert set(payload["variants_added"]) == {"ddd"}
    assert set(payload["variants_removed"]) == {"ccc"}


def test_generate_sale_toggle_payload(promotion_converted_from_sale):
    # given
    promotion = promotion_converted_from_sale
    current_info = {
        "categories": {4, 2, 3},
        "collections": set(),
        "products": {4, 5, 6, 10, 20},
        "variants": {"aaa", "bbb", "ddd"},
    }

    # when
    payload = json.loads(generate_sale_toggle_payload(promotion, current_info))[0]

    # then
    assert payload["is_active"] is True
    assert set(payload["categories"]) == current_info["categories"]
    assert not payload["collections"]
    assert set(payload["products"]) == current_info["products"]
    assert set(payload["variants"]) == current_info["variants"]
    assert graphene.Node.to_global_id("Sale", promotion.old_sale_id) == payload["id"]


@patch("saleor.webhook.payloads.serialize_checkout_lines_for_tax_calculation")
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_checkout_payload_for_tax_calculation_entire_order_voucher(
    mocked_serialize_checkout_lines_for_tax_calculation,
    mocked_fetch_checkout,
    checkout_with_prices,
    prices_entered_with_tax,
    voucher,
):
    checkout = checkout_with_prices
    currency = checkout.currency

    voucher.name = "Voucher 5 USD"
    voucher.save(update_fields=["name"])

    discount_amount = Decimal("5.00")
    checkout.voucher_code = voucher.code
    checkout.discount_amount = discount_amount
    checkout.discount_name = voucher.name
    checkout.save(update_fields=["voucher_code", "discount_amount", "discount_name"])

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    mocked_serialized_checkout_lines = {"data": "checkout_lines_data"}
    mocked_serialize_checkout_lines_for_tax_calculation.return_value = (
        mocked_serialized_checkout_lines
    )

    # when
    lines, _ = fetch_checkout_lines(checkout_with_prices)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout_with_prices, lines, manager)
    payload = json.loads(
        generate_checkout_payload_for_tax_calculation(checkout_info, lines)
    )[0]
    address = checkout.shipping_address

    # then
    shipping_price = str(
        quantize_price(
            checkout.shipping_method.channel_listings.get(
                channel_id=checkout.channel_id
            ).price.amount,
            currency,
        )
    )
    assert payload == {
        "type": "Checkout",
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", address.pk),
            "first_name": address.first_name,
            "last_name": address.last_name,
            "company_name": address.company_name,
            "street_address_1": address.street_address_1,
            "street_address_2": address.street_address_2,
            "city": address.city,
            "city_area": address.city_area,
            "postal_code": address.postal_code,
            "country": address.country.code,
            "country_area": address.country_area,
            "phone": str(address.phone),
        },
        "channel": {
            "type": "Channel",
            "id": graphene.Node.to_global_id("Channel", checkout.channel_id),
            "currency_code": checkout.channel.currency_code,
            "slug": checkout.channel.slug,
        },
        "currency": currency,
        "discounts": [{"amount": str(discount_amount), "name": voucher.name}],
        "included_taxes_in_prices": prices_entered_with_tax,
        "lines": mocked_serialized_checkout_lines,
        "metadata": {"meta_key": "meta_value"},
        "shipping_name": checkout.shipping_method.name,
        "user_id": graphene.Node.to_global_id("User", checkout.user.pk),
        "user_public_metadata": {"user_public_meta_key": "user_public_meta_value"},
        "total_amount": str(
            quantize_price(
                base_calculations.base_checkout_total(checkout_info, lines).amount,
                currency,
            )
        ),
        "shipping_amount": shipping_price,
    }
    mocked_fetch_checkout.assert_not_called()
    mocked_serialize_checkout_lines_for_tax_calculation.assert_called_once_with(
        checkout_info,
        lines,
    )


@patch("saleor.webhook.payloads.serialize_checkout_lines_for_tax_calculation")
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_checkout_payload_for_tax_calculation_specific_product_voucher(
    mocked_serialize_checkout_lines_for_tax_calculation,
    mocked_fetch_checkout,
    checkout_with_prices,
    prices_entered_with_tax,
    voucher_specific_product_type,
):
    checkout = checkout_with_prices
    currency = checkout.currency

    voucher = voucher_specific_product_type
    voucher.name = "Voucher 5 USD"
    voucher.save(update_fields=["name"])

    discount_amount = Decimal("5.00")
    checkout.voucher_code = voucher.code
    checkout.discount_amount = discount_amount
    checkout.discount_name = voucher.name
    checkout.save(update_fields=["voucher_code", "discount_amount", "discount_name"])

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    mocked_serialized_checkout_lines = {"data": "checkout_lines_data"}
    mocked_serialize_checkout_lines_for_tax_calculation.return_value = (
        mocked_serialized_checkout_lines
    )

    # when
    lines, _ = fetch_checkout_lines(checkout_with_prices)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout_with_prices, lines, manager)
    payload = json.loads(
        generate_checkout_payload_for_tax_calculation(checkout_info, lines)
    )[0]
    address = checkout.shipping_address

    # then
    shipping_price = str(
        quantize_price(
            checkout.shipping_method.channel_listings.get(
                channel_id=checkout.channel_id
            ).price.amount,
            currency,
        )
    )
    assert payload == {
        "type": "Checkout",
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", address.pk),
            "first_name": address.first_name,
            "last_name": address.last_name,
            "company_name": address.company_name,
            "street_address_1": address.street_address_1,
            "street_address_2": address.street_address_2,
            "city": address.city,
            "city_area": address.city_area,
            "postal_code": address.postal_code,
            "country": address.country.code,
            "country_area": address.country_area,
            "phone": str(address.phone),
        },
        "channel": {
            "type": "Channel",
            "id": graphene.Node.to_global_id("Channel", checkout.channel_id),
            "currency_code": checkout.channel.currency_code,
            "slug": checkout.channel.slug,
        },
        "currency": currency,
        "discounts": [],
        "included_taxes_in_prices": prices_entered_with_tax,
        "lines": mocked_serialized_checkout_lines,
        "metadata": {"meta_key": "meta_value"},
        "shipping_name": checkout.shipping_method.name,
        "user_id": graphene.Node.to_global_id("User", checkout.user.pk),
        "user_public_metadata": {"user_public_meta_key": "user_public_meta_value"},
        "total_amount": str(
            quantize_price(
                base_calculations.base_checkout_total(checkout_info, lines).amount,
                currency,
            )
        ),
        "shipping_amount": shipping_price,
    }
    mocked_fetch_checkout.assert_not_called()
    mocked_serialize_checkout_lines_for_tax_calculation.assert_called_once_with(
        checkout_info,
        lines,
    )


@patch("saleor.webhook.payloads.serialize_checkout_lines_for_tax_calculation")
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_checkout_payload_for_tax_calculation_shipping_voucher(
    mocked_serialize_checkout_lines_for_tax_calculation,
    mocked_fetch_checkout,
    checkout_with_items_and_shipping,
    prices_entered_with_tax,
    voucher_shipping_type,
    customer_user,
):
    checkout = checkout_with_items_and_shipping
    checkout.user = customer_user
    currency = checkout.currency
    voucher = voucher_shipping_type
    voucher.countries = []
    voucher.save(update_fields=["countries"])

    shipping_price = checkout.shipping_method.channel_listings.get(
        channel_id=checkout.channel_id
    ).price.amount
    assert shipping_price == Decimal(10)

    voucher_discount_amount = Decimal(3)
    listing = voucher.channel_listings.first()
    listing.discount_value = voucher_discount_amount
    listing.save(update_fields=["discount_value"])
    expected_shipping_price = quantize_price(
        shipping_price - voucher_discount_amount, currency
    )

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    mocked_serialized_checkout_lines = {"data": "checkout_lines_data"}
    mocked_serialize_checkout_lines_for_tax_calculation.return_value = (
        mocked_serialized_checkout_lines
    )

    # when
    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    add_voucher_to_checkout(
        manager, checkout_info, lines, voucher, voucher.codes.first()
    )
    payload = json.loads(
        generate_checkout_payload_for_tax_calculation(checkout_info, lines)
    )[0]
    address = checkout.shipping_address

    # then
    assert payload == {
        "type": "Checkout",
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", address.pk),
            "first_name": address.first_name,
            "last_name": address.last_name,
            "company_name": address.company_name,
            "street_address_1": address.street_address_1,
            "street_address_2": address.street_address_2,
            "city": address.city,
            "city_area": address.city_area,
            "postal_code": address.postal_code,
            "country": address.country.code,
            "country_area": address.country_area,
            "phone": str(address.phone),
        },
        "channel": {
            "type": "Channel",
            "id": graphene.Node.to_global_id("Channel", checkout.channel_id),
            "currency_code": checkout.channel.currency_code,
            "slug": checkout.channel.slug,
        },
        "currency": currency,
        "discounts": [],
        "included_taxes_in_prices": prices_entered_with_tax,
        "lines": mocked_serialized_checkout_lines,
        "metadata": {},
        "shipping_name": checkout.shipping_method.name,
        "user_id": graphene.Node.to_global_id("User", checkout.user.pk),
        "user_public_metadata": {"key": "value"},
        "total_amount": str(
            quantize_price(
                base_calculations.base_checkout_total(checkout_info, lines).amount,
                currency,
            )
        ),
        "shipping_amount": str(expected_shipping_price),
    }
    mocked_fetch_checkout.assert_not_called()
    mocked_serialize_checkout_lines_for_tax_calculation.assert_called_once_with(
        checkout_info,
        lines,
    )


@patch("saleor.webhook.payloads.serialize_checkout_lines_for_tax_calculation")
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_checkout_payload_for_tax_calculation_order_discount(
    mocked_serialize_checkout_lines_for_tax_calculation,
    mocked_fetch_checkout,
    checkout_with_prices,
    prices_entered_with_tax,
    order_promotion_rule,
):
    checkout = checkout_with_prices
    rule = order_promotion_rule
    currency = checkout.currency

    discount_amount = Decimal("5.00")
    CheckoutDiscount.objects.create(
        checkout=checkout,
        promotion_rule=rule,
        type=DiscountType.ORDER_PROMOTION,
        value_type=rule.reward_value_type,
        value=rule.reward_value,
        amount_value=discount_amount,
        currency=checkout.currency,
    )

    checkout.discount_amount = discount_amount
    checkout.discount_name = rule.name
    checkout.save(update_fields=["discount_amount", "discount_name"])

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    mocked_serialized_checkout_lines = {"data": "checkout_lines_data"}
    mocked_serialize_checkout_lines_for_tax_calculation.return_value = (
        mocked_serialized_checkout_lines
    )

    # when
    lines, _ = fetch_checkout_lines(checkout_with_prices)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout_with_prices, lines, manager)
    payload = json.loads(
        generate_checkout_payload_for_tax_calculation(checkout_info, lines)
    )[0]
    address = checkout.shipping_address

    # then
    subtotal_price = Money(0, currency)
    for line_info in lines:
        variant = line_info.variant
        variant_listing = line_info.channel_listing
        unit_price = variant.get_price(variant_listing)
        subtotal_price += unit_price * line_info.line.quantity
    shipping_price = quantize_price(
        checkout.shipping_method.channel_listings.get(
            channel_id=checkout.channel_id
        ).price.amount,
        currency,
    )
    total_price_amount = subtotal_price.amount + shipping_price
    assert payload == {
        "type": "Checkout",
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", address.pk),
            "first_name": address.first_name,
            "last_name": address.last_name,
            "company_name": address.company_name,
            "street_address_1": address.street_address_1,
            "street_address_2": address.street_address_2,
            "city": address.city,
            "city_area": address.city_area,
            "postal_code": address.postal_code,
            "country": address.country.code,
            "country_area": address.country_area,
            "phone": str(address.phone),
        },
        "channel": {
            "type": "Channel",
            "id": graphene.Node.to_global_id("Channel", checkout.channel_id),
            "currency_code": checkout.channel.currency_code,
            "slug": checkout.channel.slug,
        },
        "currency": currency,
        "discounts": [{"amount": str(discount_amount), "name": rule.name}],
        "included_taxes_in_prices": prices_entered_with_tax,
        "lines": mocked_serialized_checkout_lines,
        "metadata": {"meta_key": "meta_value"},
        "shipping_name": checkout.shipping_method.name,
        "user_id": graphene.Node.to_global_id("User", checkout.user.pk),
        "user_public_metadata": {"user_public_meta_key": "user_public_meta_value"},
        "total_amount": str(
            quantize_price(
                total_price_amount,
                currency,
            )
        ),
        "shipping_amount": str(shipping_price),
    }
    mocked_fetch_checkout.assert_not_called()
    mocked_serialize_checkout_lines_for_tax_calculation.assert_called_once_with(
        checkout_info,
        lines,
    )


@patch("saleor.webhook.payloads.serialize_checkout_lines_for_tax_calculation")
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_checkout_payload_for_tax_calculation_gift_promotion(
    mocked_serialize_checkout_lines_for_tax_calculation,
    mocked_fetch_checkout,
    checkout_with_prices,
    prices_entered_with_tax,
    gift_promotion_rule,
):
    checkout = checkout_with_prices
    currency = checkout.currency

    variants = gift_promotion_rule.gifts.all()
    variant_listings = ProductVariantChannelListing.objects.filter(variant__in=variants)
    top_price, variant_id = max(
        variant_listings.values_list("discounted_price_amount", "variant")
    )
    variant_listing = [
        listing for listing in variant_listings if listing.variant_id == variant_id
    ][0]

    line = CheckoutLine.objects.create(
        checkout=checkout,
        quantity=1,
        variant_id=variant_id,
        is_gift=True,
        currency="USD",
        undiscounted_unit_price_amount=variant_listing.price_amount,
    )

    CheckoutLineDiscount.objects.create(
        line=line,
        promotion_rule=gift_promotion_rule,
        type=DiscountType.ORDER_PROMOTION,
        value_type=RewardValueType.FIXED,
        value=top_price,
        amount_value=top_price,
        currency=checkout.channel.currency_code,
    )

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    mocked_serialized_checkout_lines = {"data": "checkout_lines_data"}
    mocked_serialize_checkout_lines_for_tax_calculation.return_value = (
        mocked_serialized_checkout_lines
    )

    # when
    lines, _ = fetch_checkout_lines(checkout_with_prices)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout_with_prices, lines, manager)
    payload = json.loads(
        generate_checkout_payload_for_tax_calculation(checkout_info, lines)
    )[0]

    # then
    subtotal_price = Money(0, currency)
    for line_info in lines:
        if line_info.line.is_gift:
            continue
        variant = line_info.variant
        variant_listing = line_info.channel_listing
        unit_price = variant.get_price(variant_listing)
        subtotal_price += unit_price * line_info.line.quantity
    shipping_price = quantize_price(
        checkout.shipping_method.channel_listings.get(
            channel_id=checkout.channel_id
        ).price.amount,
        currency,
    )
    total_price_amount = subtotal_price.amount + shipping_price
    assert payload["discounts"] == []
    assert payload["total_amount"] == str(
        quantize_price(
            total_price_amount,
            currency,
        )
    )

    mocked_fetch_checkout.assert_not_called()
    mocked_serialize_checkout_lines_for_tax_calculation.assert_called_once_with(
        checkout_info,
        lines,
    )


@patch("saleor.webhook.payloads.serialize_checkout_lines_for_tax_calculation")
def test_generate_checkout_payload_for_tax_calculation_digital_checkout(
    mocked_serialize_checkout_lines_for_tax_calculation,
    mocked_fetch_checkout,
    checkout_with_digital_item,
):
    prices_entered_with_tax = True
    checkout = checkout_with_digital_item
    currency = checkout.currency

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    mocked_serialized_checkout_lines = {"data": "checkout_lines_data"}
    mocked_serialize_checkout_lines_for_tax_calculation.return_value = (
        mocked_serialized_checkout_lines
    )
    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    payload = json.loads(
        generate_checkout_payload_for_tax_calculation(checkout_info, lines)
    )[0]
    address = checkout.billing_address

    # then
    assert payload == {
        "type": "Checkout",
        "id": graphene.Node.to_global_id("Checkout", checkout.token),
        "address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", address.pk),
            "first_name": address.first_name,
            "last_name": address.last_name,
            "company_name": address.company_name,
            "street_address_1": address.street_address_1,
            "street_address_2": address.street_address_2,
            "city": address.city,
            "city_area": address.city_area,
            "postal_code": address.postal_code,
            "country": address.country.code,
            "country_area": address.country_area,
            "phone": str(address.phone),
        },
        "channel": {
            "type": "Channel",
            "id": graphene.Node.to_global_id("Channel", checkout.channel_id),
            "currency_code": checkout.channel.currency_code,
            "slug": checkout.channel.slug,
        },
        "currency": currency,
        "discounts": [],
        "included_taxes_in_prices": prices_entered_with_tax,
        "lines": mocked_serialized_checkout_lines,
        "metadata": {},
        "shipping_name": None,
        "shipping_amount": str(quantize_price(Decimal("0.00"), currency)),
        "user_id": None,
        "user_public_metadata": {},
        "total_amount": str(
            quantize_price(
                base_calculations.base_checkout_total(checkout_info, lines).amount,
                currency,
            )
        ),
    }
    mocked_fetch_checkout.assert_not_called()
    mocked_serialize_checkout_lines_for_tax_calculation.assert_called_once_with(
        checkout_info,
        lines,
    )


@patch("saleor.webhook.payloads.serialize_checkout_lines_for_tax_calculation")
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_checkout_payload_for_tax_calculation_no_discount(
    mocked_serialize_checkout_lines_for_tax_calculation,
    mocked_fetch_checkout,
    checkout_with_prices,
    prices_entered_with_tax,
    order_promotion_rule,
):
    checkout = checkout_with_prices
    rule = order_promotion_rule
    currency = checkout.currency

    discount_amount = 0
    checkout.discount_amount = discount_amount
    checkout.discount_name = rule.name
    checkout.save(update_fields=["discount_amount", "discount_name"])

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    mocked_serialized_checkout_lines = {"data": "checkout_lines_data"}
    mocked_serialize_checkout_lines_for_tax_calculation.return_value = (
        mocked_serialized_checkout_lines
    )

    # when
    lines, _ = fetch_checkout_lines(checkout_with_prices)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout_with_prices, lines, manager)
    payload = json.loads(
        generate_checkout_payload_for_tax_calculation(checkout_info, lines)
    )[0]
    address = checkout.shipping_address

    # then
    subtotal_price = Money(0, currency)
    for line_info in lines:
        variant = line_info.variant
        variant_listing = line_info.channel_listing
        unit_price = variant.get_price(variant_listing)
        subtotal_price += unit_price * line_info.line.quantity
    shipping_price = quantize_price(
        checkout.shipping_method.channel_listings.get(
            channel_id=checkout.channel_id
        ).price.amount,
        currency,
    )
    total_price_amount = subtotal_price.amount + shipping_price
    assert payload == {
        "type": "Checkout",
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", address.pk),
            "first_name": address.first_name,
            "last_name": address.last_name,
            "company_name": address.company_name,
            "street_address_1": address.street_address_1,
            "street_address_2": address.street_address_2,
            "city": address.city,
            "city_area": address.city_area,
            "postal_code": address.postal_code,
            "country": address.country.code,
            "country_area": address.country_area,
            "phone": str(address.phone),
        },
        "channel": {
            "type": "Channel",
            "id": graphene.Node.to_global_id("Channel", checkout.channel_id),
            "currency_code": checkout.channel.currency_code,
            "slug": checkout.channel.slug,
        },
        "currency": currency,
        "discounts": [],
        "included_taxes_in_prices": prices_entered_with_tax,
        "lines": mocked_serialized_checkout_lines,
        "metadata": {"meta_key": "meta_value"},
        "shipping_name": checkout.shipping_method.name,
        "user_id": graphene.Node.to_global_id("User", checkout.user.pk),
        "user_public_metadata": {"user_public_meta_key": "user_public_meta_value"},
        "total_amount": str(
            quantize_price(
                total_price_amount,
                currency,
            )
        ),
        "shipping_amount": str(shipping_price),
    }
    mocked_fetch_checkout.assert_not_called()
    mocked_serialize_checkout_lines_for_tax_calculation.assert_called_once_with(
        checkout_info,
        lines,
    )


@freeze_time()
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_checkout_payload(
    checkout_with_prices,
    prices_entered_with_tax,
    customer_user,
):
    checkout = checkout_with_prices

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    # when
    payload = json.loads(generate_checkout_payload(checkout, customer_user))[0]

    shipping_method_channel_listing = checkout.shipping_method.channel_listings.filter(
        channel=checkout.channel,
    ).first()

    # then
    assert payload == {
        "type": "Checkout",
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "token": graphene.Node.to_global_id("Checkout", checkout.pk),
        "created": parse_django_datetime(checkout.created_at),
        "last_change": parse_django_datetime(checkout.last_change),
        "email": checkout.email,
        "currency": checkout.currency,
        "discount_amount": str(
            quantize_price(checkout.discount_amount, checkout.currency)
        ),
        "discount_name": checkout.discount_name,
        "language_code": checkout.language_code,
        "private_metadata": checkout.metadata_storage.private_metadata,
        "metadata": checkout.metadata_storage.metadata,
        "channel": {
            "type": "Channel",
            "id": graphene.Node.to_global_id("Channel", checkout.channel_id),
            "currency_code": checkout.channel.currency_code,
            "slug": checkout.channel.slug,
        },
        "user": {
            "type": "User",
            "id": graphene.Node.to_global_id("User", checkout.user.pk),
            "email": checkout.user.email,
            "first_name": checkout.user.first_name,
            "last_name": checkout.user.last_name,
        },
        "billing_address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", checkout.billing_address.pk),
            "first_name": checkout.billing_address.first_name,
            "last_name": checkout.billing_address.last_name,
            "company_name": checkout.billing_address.company_name,
            "street_address_1": checkout.billing_address.street_address_1,
            "street_address_2": checkout.billing_address.street_address_2,
            "city": checkout.billing_address.city,
            "city_area": checkout.billing_address.city_area,
            "postal_code": checkout.billing_address.postal_code,
            "country": checkout.billing_address.country.code,
            "country_area": checkout.billing_address.country_area,
            "phone": str(checkout.billing_address.phone),
        },
        "shipping_address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", checkout.shipping_address.pk),
            "first_name": checkout.shipping_address.first_name,
            "last_name": checkout.shipping_address.last_name,
            "company_name": checkout.shipping_address.company_name,
            "street_address_1": checkout.shipping_address.street_address_1,
            "street_address_2": checkout.shipping_address.street_address_2,
            "city": checkout.shipping_address.city,
            "city_area": checkout.shipping_address.city_area,
            "postal_code": checkout.shipping_address.postal_code,
            "country": checkout.shipping_address.country.code,
            "country_area": checkout.shipping_address.country_area,
            "phone": str(checkout.shipping_address.phone),
        },
        "shipping_method": {
            "id": graphene.Node.to_global_id(
                "ShippingMethod", checkout.shipping_method.pk
            ),
            "name": checkout.shipping_method.name,
            "type": checkout.shipping_method.type,
            "currency": shipping_method_channel_listing.currency,
            "price_amount": str(
                quantize_price(
                    shipping_method_channel_listing.price_amount,
                    shipping_method_channel_listing.currency,
                )
            ),
        },
        "lines": serialize_checkout_lines(checkout),
        "collection_point": json.loads(
            _generate_collection_point_payload(checkout.collection_point)
        )[0],
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
        "warehouse_address": ANY,
    }


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_generate_excluded_shipping_methods_for_order(mocked_fetch, order):
    shipping_method = ShippingMethodData(
        id="123",
        price=Money(Decimal("10.59"), "USD"),
        name="shipping",
        maximum_order_weight=Weight(kg=10),
        minimum_order_weight=Weight(g=1),
        maximum_delivery_days=10,
        minimum_delivery_days=2,
    )
    response = json.loads(
        generate_excluded_shipping_methods_for_order_payload(order, [shipping_method])
    )

    assert "order" in response
    assert response["shipping_methods"] == [
        {
            "id": graphene.Node.to_global_id("ShippingMethod", "123"),
            "price": "10.59",
            "currency": "USD",
            "name": "shipping",
            "maximum_order_weight": "10.0:kg",
            "minimum_order_weight": "1.0:g",
            "maximum_delivery_days": 10,
            "minimum_delivery_days": 2,
        }
    ]
    mocked_fetch.assert_not_called()


def test_generate_excluded_shipping_methods_for_checkout(checkout):
    shipping_method = ShippingMethodData(
        id="123",
        price=Money(Decimal("10.59"), "USD"),
        name="shipping",
        maximum_order_weight=Weight(kg=10),
        minimum_order_weight=Weight(g=1),
        maximum_delivery_days=10,
        minimum_delivery_days=2,
    )
    response = json.loads(
        generate_excluded_shipping_methods_for_checkout_payload(
            checkout, [shipping_method]
        )
    )

    assert "checkout" in response
    assert response["shipping_methods"] == [
        {
            "id": graphene.Node.to_global_id("ShippingMethod", "123"),
            "price": "10.59",
            "currency": "USD",
            "name": "shipping",
            "maximum_order_weight": "10.0:kg",
            "minimum_order_weight": "1.0:g",
            "maximum_delivery_days": 10,
            "minimum_delivery_days": 2,
        }
    ]


def test_generate_requestor_returns_dict_with_user_id_and_user_type(staff_user, rf):
    request = rf.request()
    request.user = staff_user
    request.app = None
    requestor = get_user_or_app_from_context(request)

    assert generate_requestor(requestor) == {
        "id": graphene.Node.to_global_id("User", staff_user.id),
        "type": "user",
    }


def test_generate_requestor_returns_dict_with_app_id_and_app_type(app, rf):
    request = rf.request()
    request.user = None
    request.app = app
    requestor = get_user_or_app_from_context(request)

    assert generate_requestor(requestor) == {"id": app.name, "type": "app"}


def test_generate_meta(app, rf):
    request = rf.request()
    request.app = app
    request.user = None
    requestor = get_user_or_app_from_context(request)

    meta = generate_meta(requestor_data=generate_requestor(requestor))
    assert meta["issuing_principal"] == {"id": "Sample app objects", "type": "app"}
    assert meta["version"] == __version__
    assert "issued_at" in meta


NET_AMOUNT = sentinel.NET_AMOUNT
GROSS_AMOUNT = sentinel.GROSS_AMOUNT


@pytest.mark.parametrize(
    ("action_type", "action_value"),
    [
        (TransactionAction.CHARGE, Decimal("5.000")),
        (TransactionAction.REFUND, Decimal("9.000")),
        (TransactionAction.CANCEL, None),
    ],
)
def test_generate_transaction_action_request_payload_for_order(
    action_type, action_value, order, app, rf
):
    # given
    request = rf.request()
    request.app = app
    request.user = None
    requestor = get_user_or_app_from_context(request)

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "cancel"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal(10),
    )
    requested_event = transaction.events.create(
        currency=transaction.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    # when
    payload = json.loads(
        generate_transaction_action_request_payload(
            transaction_data=TransactionActionData(
                transaction=transaction,
                action_type=action_type,
                action_value=action_value,
                event=requested_event,
                transaction_app_owner=None,
            ),
            requestor=requestor,
        )
    )

    # then
    currency = transaction.currency
    action_value = str(quantize_price(action_value, currency)) if action_value else None
    del payload["meta"]["issued_at"]
    assert payload == {
        "action": {
            "type": action_type,
            "value": action_value,
            "currency": currency,
        },
        "transaction": {
            "type": transaction.name,
            "name": transaction.name,
            "message": transaction.message,
            "reference": transaction.psp_reference,
            "psp_reference": transaction.psp_reference,
            "available_actions": transaction.available_actions,
            "currency": currency,
            "charged_value": str(quantize_price(transaction.charged_value, currency)),
            "authorized_value": str(
                quantize_price(transaction.authorized_value, currency)
            ),
            "refunded_value": str(quantize_price(transaction.refunded_value, currency)),
            "canceled_value": str(quantize_price(transaction.canceled_value, currency)),
            "order_id": graphene.Node.to_global_id("Order", order.pk),
            "checkout_id": None,
            "created_at": parse_django_datetime(transaction.created_at),
            "modified_at": parse_django_datetime(transaction.modified_at),
        },
        "meta": {
            "issuing_principal": {"id": "Sample app objects", "type": "app"},
            "version": __version__,
        },
    }


@pytest.mark.parametrize(
    ("action_type", "request_type", "action_value"),
    [
        (
            TransactionAction.CHARGE,
            TransactionEventType.CHARGE_REQUEST,
            Decimal("5.000"),
        ),
        (
            TransactionAction.REFUND,
            TransactionEventType.REFUND_REQUEST,
            Decimal("9.000"),
        ),
        (TransactionAction.CANCEL, TransactionEventType.CANCEL_REQUEST, None),
    ],
)
def test_generate_transaction_action_request_payload_for_checkout(
    action_type, request_type, action_value, checkout, app, rf
):
    # given
    request = rf.request()
    request.app = app
    request.user = None
    requestor = get_user_or_app_from_context(request)

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "cancel"],
        currency="USD",
        checkout_id=checkout.pk,
        authorized_value=Decimal(10),
    )
    requested_event = transaction.events.create(
        currency=transaction.currency,
        type=request_type,
    )

    # when
    payload = json.loads(
        generate_transaction_action_request_payload(
            transaction_data=TransactionActionData(
                transaction=transaction,
                action_type=action_type,
                action_value=action_value,
                event=requested_event,
                transaction_app_owner=None,
            ),
            requestor=requestor,
        )
    )

    # then
    currency = transaction.currency
    action_value = str(quantize_price(action_value, currency)) if action_value else None
    del payload["meta"]["issued_at"]
    assert payload == {
        "action": {
            "type": action_type,
            "value": action_value,
            "currency": currency,
        },
        "transaction": {
            "type": transaction.name,
            "name": transaction.name,
            "message": transaction.message,
            "reference": transaction.psp_reference,
            "psp_reference": transaction.psp_reference,
            "available_actions": transaction.available_actions,
            "currency": currency,
            "charged_value": str(quantize_price(transaction.charged_value, currency)),
            "authorized_value": str(
                quantize_price(transaction.authorized_value, currency)
            ),
            "refunded_value": str(quantize_price(transaction.refunded_value, currency)),
            "canceled_value": str(quantize_price(transaction.canceled_value, currency)),
            "order_id": None,
            "checkout_id": graphene.Node.to_global_id("Checkout", checkout.pk),
            "created_at": parse_django_datetime(transaction.created_at),
            "modified_at": parse_django_datetime(transaction.modified_at),
        },
        "meta": {
            "issuing_principal": {"id": "Sample app objects", "type": "app"},
            "version": __version__,
        },
    }


@freeze_time()
def test_generate_warehouse_metadata_updated_payload(
    warehouse,
    customer_user,
):
    # when
    payload = json.loads(generate_metadata_updated_payload(warehouse, customer_user))[0]

    # then
    assert payload == {
        "id": graphene.Node.to_global_id("Warehouse", warehouse.id),
        "meta": generate_meta(requestor_data=generate_requestor(customer_user)),
    }


def test_generate_thumbnail_payload(thumbnail_product_media):
    # given
    thumbnail = thumbnail_product_media
    thumbnail_id = graphene.Node.to_global_id("Thumbnail", thumbnail.id)

    expected_payload = {"id": thumbnail_id}

    # when
    payload = json.loads(generate_thumbnail_payload(thumbnail))

    # then
    assert payload == expected_payload


def test_generate_product_media_payload(product_media_image):
    # given
    media = product_media_image
    media_id = graphene.Node.to_global_id("ProductMedia", media.id)

    expected_payload = {"id": media_id}

    # when
    payload = json.loads(generate_product_media_payload(media))

    # then
    assert payload == expected_payload
