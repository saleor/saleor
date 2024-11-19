import datetime
from decimal import Decimal
from unittest import mock
from unittest.mock import patch

import before_after
import graphene
import pytest
from django.test import override_settings
from django.utils import timezone
from prices import Money

from .....checkout import base_calculations, calculations
from .....checkout.actions import call_checkout_info_event
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.utils import add_variant_to_checkout, set_external_shipping_id
from .....core.models import EventDelivery
from .....discount import VoucherType
from .....plugins.manager import get_plugins_manager
from .....product.models import (
    Collection,
    ProductChannelListing,
    ProductVariantChannelListing,
)
from .....warehouse.models import Stock
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_CHECKOUT_ADD_PROMO_CODE = """
    mutation($id: ID, $promoCode: String!) {
        checkoutAddPromoCode(
            id: $id, promoCode: $promoCode) {
            errors {
                field
                message
                code
            }
            checkout {
                id
                token
                voucherCode
                lines {
                    id
                }
                discount {
                    amount
                }
                giftCards {
                    id
                    last4CodeChars
                }
                totalPrice {
                    gross {
                        amount
                    }
                }
                availableShippingMethods {
                    id
                    price {
                        amount
                    }
                }
                shippingMethod {
                    id
                    price {
                        amount
                    }
                }
                subtotalPrice {
                    gross {
                        amount
                    }
                }
            }
        }
    }
"""


def _mutate_checkout_add_promo_code(client, variables):
    response = client.post_graphql(MUTATION_CHECKOUT_ADD_PROMO_CODE, variables)
    content = get_graphql_content(response)
    return content["data"]["checkoutAddPromoCode"]


def test_checkout_add_voucher_for_entire_order(api_client, checkout_with_item, voucher):
    # given
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher.code,
    }
    assert voucher.type == VoucherType.ENTIRE_ORDER
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    taxed_total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    checkout_with_item.refresh_from_db()
    assert not data["errors"]
    checkout_data = data["checkout"]
    total_price_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert (
        total_price_gross_amount
        == taxed_total.gross.amount - checkout_with_item.discount_amount
    )


def test_checkout_add_voucher_code_by_token(api_client, checkout_with_item, voucher):
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert data["checkout"]["voucherCode"] == voucher.code


def test_checkout_add_already_applied_voucher_for_entire_order(
    api_client, checkout_with_item, voucher
):
    # given
    variant = checkout_with_item.lines.first().variant
    channel = checkout_with_item.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing) * checkout_with_item.lines.first().quantity

    voucher_channel_listing = voucher.channel_listings.get(channel=channel)
    voucher_channel_listing.discount_value = net.amount
    voucher_channel_listing.save(update_fields=["discount_value"])

    checkout_with_item.voucher_code = voucher.code
    checkout_with_item.discount_amount = net.amount
    checkout_with_item.save()

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher.code,
    }
    assert voucher.type == VoucherType.ENTIRE_ORDER

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    checkout_with_item.refresh_from_db()
    assert not data["errors"]
    checkout_data = data["checkout"]
    total_price_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_price_gross_amount == 0
    assert checkout_data["discount"]["amount"] == net.amount


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_checkout_add_voucher_code_by_token_with_external_shipment(
    mock_send_request,
    api_client,
    checkout_with_item,
    voucher,
    shipping_app,
    address,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "abcd"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": "Provider - Economy",
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    mock_send_request.return_value = mock_json_response

    external_shipping_method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    checkout = checkout_with_item
    checkout.shipping_address = address
    set_external_shipping_id(checkout, external_shipping_method_id)
    checkout.save(update_fields=["shipping_address"])
    checkout.metadata_storage.save(update_fields=["private_metadata"])

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert data["checkout"]["voucherCode"] == voucher.code
    assert data["checkout"]["shippingMethod"]["id"] == external_shipping_method_id


def test_checkout_add_voucher_code_with_display_gross_prices(
    api_client, checkout_with_item, voucher, site_settings, monkeypatch
):
    channel = checkout_with_item.channel
    tc = channel.tax_configuration
    tc.display_gross_prices = True
    tc.save(update_fields=["display_gross_prices"])
    tc.country_exceptions.all().delete()

    previous_checkout_last_change = checkout_with_item.last_change

    voucher = voucher
    voucher_channel_listing = voucher.channel_listings.first()
    voucher_channel_listing.min_spent_amount = 100
    voucher_channel_listing.save()

    monkeypatch.setattr(
        "saleor.checkout.utils.base_calculations.base_checkout_subtotal",
        lambda *args: Money(100, "USD"),
    )

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert data["checkout"]["voucherCode"] == voucher.code
    checkout_with_item.refresh_from_db()
    assert checkout_with_item.last_change != previous_checkout_last_change


def test_checkout_add_voucher_code_without_display_gross_prices(
    api_client, checkout_with_item, voucher, site_settings, monkeypatch
):
    channel = checkout_with_item.channel
    tc = channel.tax_configuration
    tc.display_gross_prices = False
    tc.save(update_fields=["display_gross_prices"])
    tc.country_exceptions.all().delete()

    previous_checkout_last_change = checkout_with_item.last_change

    voucher = voucher
    voucher_channel_listing = voucher.channel_listings.first()
    voucher_channel_listing.min_spent_amount = 100
    voucher_channel_listing.save()

    monkeypatch.setattr(
        "saleor.checkout.utils.base_calculations.base_checkout_subtotal",
        lambda *args: Money(95, "USD"),
    )

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"][0]["code"] == CheckoutErrorCode.VOUCHER_NOT_APPLICABLE.name
    assert data["errors"][0]["field"] == "promoCode"

    checkout_with_item.refresh_from_db()
    assert checkout_with_item.last_change == previous_checkout_last_change


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_checkout_add_voucher_code_line_without_listing(
    channel_listing_model, listing_filter_field, api_client, checkout_with_item, voucher
):
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher.code,
    }
    line = checkout_with_item.lines.first()
    channel_listing_model.objects.filter(
        channel_id=checkout_with_item.channel_id,
        **{listing_filter_field: line.variant_id},
    ).delete()
    data = _mutate_checkout_add_promo_code(api_client, variables)

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"


def test_checkout_add_voucher_code_checkout_with_sale(
    api_client, checkout_with_item_on_sale, voucher_percentage, channel_USD
):
    # given
    checkout = checkout_with_item_on_sale
    manager = get_plugins_manager(allow_replica=False)
    address = checkout.shipping_address

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout_info.checkout.price_expiration = timezone.now()

    subtotal_discounted = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )

    voucher_discount_value = (
        voucher_percentage.channel_listings.filter(channel=checkout.channel)
        .first()
        .discount_value
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": voucher_percentage.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    discounted_subtotal = (
        lines[0].channel_listing.discounted_price_amount * lines[0].line.quantity
    )
    voucher_discount = voucher_discount_value / 100 * discounted_subtotal

    previous_checkout_last_change = checkout.last_change

    checkout.refresh_from_db()
    assert not data["errors"]
    assert checkout.voucher_code == voucher_percentage.code
    assert checkout.discount_amount == voucher_discount
    assert checkout.last_change != previous_checkout_last_change
    assert checkout.subtotal < subtotal_discounted


def test_checkout_add_specific_product_voucher_code_checkout_with_sale(
    api_client, checkout_with_item_on_sale, voucher_specific_product_type
):
    # given
    voucher = voucher_specific_product_type
    checkout = checkout_with_item_on_sale
    expected_discount = Decimal(1.5)
    manager = get_plugins_manager(allow_replica=False)

    checkout.price_expiration = timezone.now()

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    subtotal_discounted = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": voucher.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    subtotal_with_voucher = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    assert not data["errors"]
    assert subtotal_discounted == subtotal_with_voucher + Money(
        expected_discount, "USD"
    )
    assert checkout.voucher_code == voucher.code
    assert checkout.discount_amount == expected_discount


def test_checkout_add_products_voucher_code_checkout_with_sale(
    api_client, checkout_with_item_on_sale, voucher_percentage, channel_USD
):
    # given
    checkout = checkout_with_item_on_sale
    product = checkout.lines.first().variant.product
    voucher = voucher_percentage
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()
    voucher.products.add(product)

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    checkout.price_expiration = timezone.now()
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    subtotal_discounted = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )

    voucher_discount_value = (
        voucher_percentage.channel_listings.filter(channel=checkout.channel)
        .first()
        .discount_value
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": voucher.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    discounted_subtotal = (
        lines[0].channel_listing.discounted_price_amount * lines[0].line.quantity
    )
    voucher_discount = voucher_discount_value / 100 * discounted_subtotal

    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    subtotal_with_voucher = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    assert not data["errors"]
    assert subtotal_discounted == subtotal_with_voucher + Money(
        voucher_discount, checkout.currency
    )
    assert checkout.voucher_code == voucher.code
    assert checkout.discount_amount == voucher_discount
    assert checkout.subtotal < subtotal_discounted


def test_checkout_add_collection_voucher_code_checkout_with_sale(
    api_client, checkout_with_item_on_sale, voucher_percentage, collection
):
    # given
    checkout = checkout_with_item_on_sale

    voucher = voucher_percentage
    product = checkout.lines.first().variant.product
    product.collections.add(collection)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()
    voucher.collections.add(collection)

    voucher_discount_value = (
        voucher_percentage.channel_listings.filter(channel=checkout.channel)
        .first()
        .discount_value
    )

    manager = get_plugins_manager(allow_replica=False)

    checkout.price_expiration = timezone.now()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    subtotal_discounted = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": voucher.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    discounted_subtotal = (
        lines[0].channel_listing.discounted_price_amount * lines[0].line.quantity
    )
    voucher_discount = voucher_discount_value / 100 * discounted_subtotal

    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    subtotal_with_voucher = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )

    assert not data["errors"]
    assert subtotal_discounted == subtotal_with_voucher + Money(
        voucher_discount, checkout.currency
    )
    assert checkout.voucher_code == voucher.code
    assert checkout.discount_amount == voucher_discount


def test_checkout_add_collection_voucher_code_checkout_with_sale_collection_deleted(
    api_client, checkout_with_item_on_sale, voucher_percentage, collection
):
    # given
    checkout = checkout_with_item_on_sale

    voucher = voucher_percentage
    product = checkout.lines.first().variant.product
    product.collections.add(collection)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()
    voucher.collections.add(collection)
    checkout.price_expiration = timezone.now()
    lines, _ = fetch_checkout_lines(checkout)
    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": voucher.code,
    }
    assert Collection.objects.count() == 1

    # when
    def delete_collections(*args, **kwargs):
        Collection.objects.all().delete()

    with before_after.after(
        "saleor.graphql.product.dataloaders.products.CollectionsByProductIdLoader"
        ".batch_load",
        delete_collections,
    ):
        data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    assert not data["errors"]
    assert Collection.objects.count() == 0


def test_checkout_add_category_code_checkout_with_sale(
    api_client, checkout_with_item_on_sale, voucher_percentage, channel_USD
):
    # given
    checkout = checkout_with_item_on_sale
    product = checkout.lines.first().variant.product
    category = product.category
    voucher = voucher_percentage
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()
    voucher.categories.add(category)

    voucher_discount_value = (
        voucher_percentage.channel_listings.filter(channel=checkout.channel)
        .first()
        .discount_value
    )

    checkout.price_expiration = timezone.now()
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    subtotal_discounted = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": voucher.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    discounted_subtotal = (
        lines[0].channel_listing.discounted_price_amount * lines[0].line.quantity
    )
    voucher_discount = voucher_discount_value / 100 * discounted_subtotal

    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    subtotal_with_voucher = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    assert not data["errors"]
    assert subtotal_discounted == subtotal_with_voucher + Money(
        voucher_discount, checkout.currency
    )
    assert checkout.voucher_code == voucher.code
    assert checkout.discount_amount == voucher_discount
    assert checkout.subtotal < subtotal_discounted


def test_checkout_add_voucher_code_checkout_on_promotion(
    api_client, checkout_with_item_on_promotion, voucher_percentage, channel_USD
):
    # given
    checkout = checkout_with_item_on_promotion
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    address = checkout.shipping_address

    voucher_discount_value = (
        voucher_percentage.channel_listings.filter(channel=checkout.channel)
        .first()
        .discount_value
    )

    # when
    checkout_info.checkout.price_expiration = timezone.now()
    subtotal_discounted = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": voucher_percentage.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    previous_checkout_last_change = checkout.last_change

    discounted_subtotal = (
        lines[0].channel_listing.discounted_price_amount * lines[0].line.quantity
    )
    voucher_discount = voucher_discount_value / 100 * discounted_subtotal

    checkout.refresh_from_db()
    assert not data["errors"]
    assert checkout.voucher_code == voucher_percentage.code
    assert checkout.discount_amount == voucher_discount
    assert checkout.last_change != previous_checkout_last_change
    assert checkout.subtotal < subtotal_discounted


def test_checkout_add_specific_product_voucher_code_checkout_on_promotion(
    api_client,
    checkout_with_item_on_promotion,
    voucher_specific_product_type,
    product,
    channel_USD,
):
    # given
    voucher = voucher_specific_product_type
    checkout = checkout_with_item_on_promotion
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    voucher_discount_value = (
        voucher_specific_product_type.channel_listings.filter(channel=checkout.channel)
        .first()
        .discount_value
    )

    checkout.price_expiration = timezone.now()
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    subtotal_discounted = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": voucher.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    discounted_subtotal = (
        lines[0].channel_listing.discounted_price_amount * lines[0].line.quantity
    )
    voucher_discount = voucher_discount_value / 100 * discounted_subtotal

    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    subtotal_with_voucher = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    assert not data["errors"]
    assert subtotal_discounted == subtotal_with_voucher + Money(
        voucher_discount, checkout.currency
    )
    assert checkout.voucher_code == voucher.code
    assert checkout.discount_amount == voucher_discount


def test_checkout_add_collection_voucher_code_checkout_on_promotion(
    api_client,
    checkout_with_item_on_promotion,
    voucher_percentage,
    collection,
    channel_USD,
):
    # given
    checkout = checkout_with_item_on_promotion
    voucher = voucher_percentage

    product = checkout.lines.first().variant.product
    product.collections.add(collection)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()

    voucher.collections.add(collection)

    voucher_discount_value = (
        voucher_percentage.channel_listings.filter(channel=checkout.channel)
        .first()
        .discount_value
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    checkout.price_expiration = timezone.now()

    subtotal_discounted = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": voucher.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    discounted_subtotal = (
        lines[0].channel_listing.discounted_price_amount * lines[0].line.quantity
    )
    voucher_discount = voucher_discount_value / 100 * discounted_subtotal

    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    subtotal_with_voucher = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )

    assert not data["errors"]
    assert subtotal_discounted == subtotal_with_voucher + Money(
        voucher_discount, checkout.currency
    )
    assert checkout.voucher_code == voucher.code
    assert checkout.discount_amount == voucher_discount


def test_checkout_add_category_code_checkout_on_promotion(
    api_client, checkout_with_item_on_promotion, voucher_percentage, channel_USD
):
    # given
    checkout = checkout_with_item_on_promotion

    product = checkout.lines.first().variant.product
    category = product.category
    voucher = voucher_percentage
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()
    voucher.categories.add(category)

    voucher_discount_value = (
        voucher_percentage.channel_listings.filter(channel=checkout.channel)
        .first()
        .discount_value
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    checkout.price_expiration = timezone.now()
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    subtotal_discounted = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": voucher.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    discounted_subtotal = (
        lines[0].channel_listing.discounted_price_amount * lines[0].line.quantity
    )
    voucher_discount = voucher_discount_value / 100 * discounted_subtotal

    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    subtotal_with_voucher = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    assert not data["errors"]
    assert subtotal_discounted == subtotal_with_voucher + Money(
        voucher_discount, checkout.currency
    )
    assert checkout.voucher_code == voucher.code
    assert checkout.discount_amount == voucher_discount
    assert checkout.subtotal < subtotal_discounted


def test_checkout_add_voucher_code_checkout_on_order_promotion_discount(
    api_client, checkout_with_item_and_order_discount, voucher
):
    # given
    checkout = checkout_with_item_and_order_discount
    checkout_discount = checkout.discounts.first()
    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": voucher.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout.token)
    assert data["checkout"]["voucherCode"] == voucher.code
    checkout.refresh_from_db()
    assert not checkout.discounts.all()
    assert checkout.discount_amount
    assert checkout.discount_name == voucher.name
    with pytest.raises(checkout_discount._meta.model.DoesNotExist):
        checkout_discount.refresh_from_db()


def test_checkout_add_voucher_code_checkout_with_gift_reward(
    api_client, checkout_with_item_and_gift_promotion, voucher
):
    # given
    checkout = checkout_with_item_and_gift_promotion
    gift_line = checkout.lines.get(is_gift=True)
    line_discount = gift_line.discounts.first()

    lines_count = checkout.lines.count()

    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": voucher.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout.token)
    assert data["checkout"]["voucherCode"] == voucher.code
    checkout.refresh_from_db()
    assert checkout.lines.count() == lines_count - 1 == len(data["checkout"]["lines"])
    assert checkout.discount_amount
    assert checkout.discount_name == voucher.name
    with pytest.raises(line_discount._meta.model.DoesNotExist):
        line_discount.refresh_from_db()
    with pytest.raises(gift_line._meta.model.DoesNotExist):
        gift_line.refresh_from_db()


def test_checkout_add_variant_voucher_code_apply_once_per_order(
    api_client, checkout_with_items, voucher_specific_product_type
):
    # given
    checkout = checkout_with_items
    channel = checkout.channel

    lines = checkout.lines.all()
    checkout.lines.last().delete()
    variant_1, variant_2, variant_3 = (line.variant for line in lines)
    variant_1_listing = variant_1.channel_listings.get(channel=channel)
    variant_2_listing = variant_2.channel_listings.get(channel=channel)
    variant_3_listing = variant_3.channel_listings.get(channel=channel)

    variant_1_price = Decimal(10)
    variant_2_price = Decimal(25)
    variant_3_price = Decimal(20)
    variant_1_listing.price_amount = variant_1_price
    variant_2_listing.price_amount = variant_2_price
    variant_3_listing.price_amount = variant_3_price

    variant_1_listing.price_amount = variant_1_price
    variant_2_listing.discounted_price_amount = variant_2_price
    variant_3_listing.discounted_price_amount = variant_3_price

    ProductVariantChannelListing.objects.bulk_update(
        [variant_1_listing, variant_2_listing, variant_3_listing],
        ["price_amount", "discounted_price_amount"],
    )

    voucher = voucher_specific_product_type
    voucher.apply_once_per_order = True
    voucher.save(update_fields=["apply_once_per_order"])

    voucher_listing = voucher.channel_listings.get(channel=channel)
    discount_value = 20
    voucher_listing.discount_value = discount_value
    voucher_listing.save(update_fields=["discount_value"])

    voucher.variants.set([variant_2, variant_3])
    voucher.products.clear()

    expected_discount = Money(
        variant_3_price * (Decimal(discount_value) / 100), checkout.currency
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout.price_expiration = timezone.now()
    subtotal_before_voucher = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": voucher.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    assert not data["errors"]
    assert checkout.voucher_code == voucher.code
    assert checkout.discount_amount == expected_discount.amount
    assert checkout.subtotal + expected_discount == subtotal_before_voucher


def test_checkout_add_voucher_code_not_applicable_voucher(
    api_client, checkout_with_item, voucher_with_high_min_spent_amount
):
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher_with_high_min_spent_amount.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_voucher_code_not_assigned_to_channel(
    api_client, checkout_with_item, voucher_without_channel
):
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher_without_channel.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_voucher_code_lack_of_active_codes(
    api_client, checkout_with_item, voucher_percentage
):
    # given
    voucher_percentage.single_use = True
    voucher_percentage.save(update_fields=["single_use"])

    voucher_percentage.codes.update(is_active=False)

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher_percentage.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    assert data["errors"]
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_gift_card_code(api_client, checkout_with_item, gift_card):
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": gift_card.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert data["checkout"]["giftCards"][0]["id"] == gift_card_id
    assert data["checkout"]["giftCards"][0]["last4CodeChars"] == gift_card.display_code


def test_checkout_add_many_gift_card_code(
    api_client, checkout_with_gift_card, gift_card_created_by_staff
):
    assert checkout_with_gift_card.gift_cards.count() > 0
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_created_by_staff.pk)
    variables = {
        "id": to_global_id_or_none(checkout_with_gift_card),
        "promoCode": gift_card_created_by_staff.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_gift_card.token)
    gift_card_data = data["checkout"]["giftCards"]
    assert gift_card_id in {gift_card["id"] for gift_card in gift_card_data}


def test_checkout_add_inactive_gift_card_code(
    staff_api_client, checkout_with_item, gift_card
):
    # given
    gift_card.is_active = False
    gift_card.save(update_fields=["is_active"])

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": gift_card.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(staff_api_client, variables)

    # then
    assert not data["checkout"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CheckoutErrorCode.INVALID.name
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_expired_gift_card_code(
    staff_api_client, checkout_with_item, gift_card
):
    # given
    gift_card.expiry_date = datetime.datetime.now(
        tz=datetime.UTC
    ).date() - datetime.timedelta(days=10)
    gift_card.save(update_fields=["expiry_date"])

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": gift_card.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(staff_api_client, variables)

    # then
    assert not data["checkout"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CheckoutErrorCode.INVALID.name
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_used_gift_card_code(
    staff_api_client, checkout_with_item, gift_card_used, customer_user
):
    # given
    checkout_with_item.email = gift_card_used.used_by_email
    checkout_with_item.save(update_fields=["email"])

    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_used.pk)

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": gift_card_used.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(staff_api_client, variables)

    # then
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert data["checkout"]["giftCards"][0]["id"] == gift_card_id
    assert (
        data["checkout"]["giftCards"][0]["last4CodeChars"]
        == gift_card_used.display_code
    )


def test_checkout_get_total_with_gift_card(api_client, checkout_with_item, gift_card):
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    taxed_total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    total_with_gift_card = taxed_total.gross.amount - gift_card.current_balance_amount

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": gift_card.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert not data["checkout"]["giftCards"] == []
    assert data["checkout"]["totalPrice"]["gross"]["amount"] == total_with_gift_card


def test_checkout_get_total_with_many_gift_card(
    api_client, checkout_with_gift_card, gift_card_created_by_staff
):
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_gift_card)
    checkout_info = fetch_checkout_info(checkout_with_gift_card, lines, manager)
    taxed_total = calculations.calculate_checkout_total_with_gift_cards(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_gift_card.shipping_address,
    )
    total_with_gift_card = (
        taxed_total.gross.amount - gift_card_created_by_staff.current_balance_amount
    )

    assert checkout_with_gift_card.gift_cards.count() > 0
    variables = {
        "id": to_global_id_or_none(checkout_with_gift_card),
        "promoCode": gift_card_created_by_staff.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_gift_card.token)
    assert data["checkout"]["totalPrice"]["gross"]["amount"] == total_with_gift_card


def test_checkout_get_total_with_more_money_on_gift_card(
    api_client, checkout_with_item, gift_card_used, customer_user
):
    checkout_with_item.email = gift_card_used.used_by_email
    checkout_with_item.save(update_fields=["email"])

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": gift_card_used.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert not data["checkout"]["giftCards"] == []
    assert data["checkout"]["totalPrice"]["gross"]["amount"] == 0


def test_checkout_add_same_gift_card_code(api_client, checkout_with_gift_card):
    gift_card = checkout_with_gift_card.gift_cards.first()
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    gift_card_count = checkout_with_gift_card.gift_cards.count()
    variables = {
        "id": to_global_id_or_none(checkout_with_gift_card),
        "promoCode": gift_card.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_gift_card.token)
    assert data["checkout"]["giftCards"][0]["id"] == gift_card_id
    assert data["checkout"]["giftCards"][0]["last4CodeChars"] == gift_card.display_code
    assert len(data["checkout"]["giftCards"]) == gift_card_count


def test_checkout_add_gift_card_code_in_active_gift_card(
    api_client, checkout_with_item, gift_card
):
    gift_card.is_active = False
    gift_card.save()

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": gift_card.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_gift_card_code_in_expired_gift_card(
    api_client, checkout_with_item, gift_card
):
    gift_card.expiry_date = datetime.datetime.now(
        tz=datetime.UTC
    ).date() - datetime.timedelta(days=1)
    gift_card.save()

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": gift_card.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_promo_code_invalid_checkout(api_client, voucher, checkout):
    variables = {"id": to_global_id_or_none(checkout), "promoCode": voucher.code}
    checkout.delete()
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["field"] == "id"


def test_checkout_add_promo_code_invalid_promo_code(api_client, checkout_with_item):
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": "unexisting_code",
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_promo_code_invalidate_shipping_method(
    api_client,
    checkout,
    variant_with_many_stocks_different_shipping_zones,
    gift_card_created_by_staff,
    address_usa,
    shipping_method,
    channel_USD,
    voucher,
):
    Stock.objects.update(quantity=5)

    # Free shipping for 50 USD
    shipping_channel_listing = shipping_method.channel_listings.first()
    shipping_channel_listing.minimum_order_price = Money(50, "USD")
    shipping_channel_listing.price = Money(0, "USD")
    shipping_channel_listing.save()

    # Setup checkout with items worth $50
    checkout.shipping_address = address_usa
    checkout.shipping_method = shipping_method
    checkout.billing_address = address_usa
    checkout.save()

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    variant = variant_with_many_stocks_different_shipping_zones
    add_variant_to_checkout(checkout_info, variant, 5)
    checkout.save()

    # Apply voucher
    variables = {"id": to_global_id_or_none(checkout), "promoCode": voucher.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    assert data["checkout"]["shippingMethod"] is None
    assert shipping_method_id not in data["checkout"]["availableShippingMethods"]


def test_checkout_add_promo_code_without_checkout_email(
    api_client, checkout_with_item, voucher
):
    # given
    checkout_with_item.email = None
    checkout_with_item.save(update_fields=["email"])

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    assert not data["errors"]
    assert data["checkout"]["voucherCode"] == voucher.code


def test_checkout_add_gift_card_without_checkout_email(
    api_client, checkout_with_item, gift_card
):
    # given
    checkout_with_item.email = None
    checkout_with_item.save(update_fields=["email"])
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": gift_card.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert data["checkout"]["giftCards"][0]["id"] == gift_card_id
    assert data["checkout"]["giftCards"][0]["last4CodeChars"] == gift_card.display_code


def test_checkout_add_gift_card_without_checkout_email_used_by_someone_else_email(
    api_client, checkout_with_item, gift_card
):
    # given
    checkout_with_item.email = None
    checkout_with_item.save(update_fields=["email"])
    gift_card.used_by_email = "nonexisting@example.com"
    gift_card.save(update_fields=["used_by_email"])
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": gift_card.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert data["checkout"]["giftCards"][0]["id"] == gift_card_id
    assert data["checkout"]["giftCards"][0]["last4CodeChars"] == gift_card.display_code


def test_checkout_add_gift_card_without_checkout_email_used_by_other_user(
    api_client, checkout_with_item, gift_card, customer_user
):
    # given
    checkout_with_item.email = None
    checkout_with_item.save(update_fields=["email"])
    gift_card.used_by = customer_user
    gift_card.save(update_fields=["used_by"])
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": gift_card.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert data["checkout"]["giftCards"][0]["id"] == gift_card_id
    assert data["checkout"]["giftCards"][0]["last4CodeChars"] == gift_card.display_code


@pytest.mark.parametrize("shipping_price", [12, 10, 5])
def test_checkout_add_free_shipping_voucher_do_not_invalidate_shipping_method(
    shipping_price,
    api_client,
    checkout_with_item,
    voucher_free_shipping,
    shipping_method,
    address_usa,
):
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.shipping_address = address_usa
    checkout_with_item.save(update_fields=["shipping_method", "shipping_address"])

    channel = checkout_with_item.channel

    line = checkout_with_item.lines.first()
    line.quantity = 1
    line.save(update_fields=["quantity"])

    variant_listing = line.variant.channel_listings.get(channel=channel)
    variant_listing.price = Money(10, "USD")
    variant_listing.save(update_fields=["price_amount"])

    # set minimal price similar to order subtotal price;
    # set shipping price so big, that in case the discount will be applied
    # substracted from subtotal the shipping method will be not valid anymore
    shipping_listing = shipping_method.channel_listings.get(channel=channel)
    shipping_listing.price = Money(shipping_price, "USD")
    shipping_listing.minimum_order_price = Money(8, "USD")
    shipping_listing.save(update_fields=["price_amount", "minimum_order_price_amount"])

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher_free_shipping.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # ensure that shipping method wasn't invalidate
    assert data["checkout"]["shippingMethod"]["id"] == graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.id
    )


@pytest.mark.parametrize("shipping_discount", [12, 10, 5])
def test_checkout_add_shipping_voucher_do_not_invalidate_shipping_method(
    shipping_discount,
    api_client,
    checkout_with_item,
    voucher_shipping_type,
    shipping_method,
    address_usa,
):
    """Ensure that adding shipping voucher do not invalidate current shipping method."""
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.shipping_address = address_usa
    checkout_with_item.save(update_fields=["shipping_method", "shipping_address"])

    channel = checkout_with_item.channel

    line = checkout_with_item.lines.first()
    line.quantity = 1
    line.save(update_fields=["quantity"])

    variant_listing = line.variant.channel_listings.get(channel=channel)
    variant_listing.price = Money(10, "USD")
    variant_listing.save(update_fields=["price_amount"])

    # set minimal price similar to order subtotal price;
    shipping_listing = shipping_method.channel_listings.get(channel=channel)
    shipping_listing.price = Money(20, "USD")
    shipping_listing.minimum_order_price = Money(8, "USD")
    shipping_listing.save(update_fields=["price_amount", "minimum_order_price_amount"])

    # set shipping voucher price so big, that in case the discount will be
    # substracted from subtotal price the shipping method will be not valid anymore
    voucher_listing = voucher_shipping_type.channel_listings.get(channel=channel)
    voucher_listing.discount = Money(shipping_discount, "USD")
    voucher_listing.save(update_fields=["discount_value"])

    voucher_shipping_type.countries = []
    voucher_shipping_type.save(update_fields=["countries"])

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher_shipping_type.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # ensure that shipping method wasn't invalidate
    assert data["checkout"]["shippingMethod"]["id"] == graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.id
    )


def test_checkout_add_voucher_code_invalidates_price(
    api_client, checkout_with_item, voucher
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    subtotal = base_calculations.base_checkout_subtotal(
        lines,
        checkout_info.channel,
        checkout_info.checkout.currency,
    )
    expected_total = subtotal.amount - voucher.channel_listings.get().discount.amount
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher.code,
    }

    # when
    data = _mutate_checkout_add_promo_code(api_client, variables)

    # then
    assert not data["errors"]
    assert data["checkout"]["voucherCode"] == voucher.code
    assert data["checkout"]["subtotalPrice"]["gross"]["amount"] == expected_total
    assert data["checkout"]["totalPrice"]["gross"]["amount"] == expected_total


def test_with_active_problems_flow(
    api_client,
    checkout_with_problems,
    voucher,
):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    variables = {
        "id": to_global_id_or_none(checkout_with_problems),
        "promoCode": voucher.code,
    }

    # when
    response = api_client.post_graphql(
        MUTATION_CHECKOUT_ADD_PROMO_CODE,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutAddPromoCode"]["errors"]


@patch(
    "saleor.graphql.checkout.mutations.checkout_add_promo_code.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_add_voucher_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_info_event,
    setup_checkout_webhooks,
    settings,
    api_client,
    checkout_with_item,
    voucher,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher.code,
    }

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_ADD_PROMO_CODE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutAddPromoCode"]["errors"]

    assert wrapped_call_checkout_info_event.called

    # confirm that event delivery was generated for each async webhook.
    checkout_update_delivery = EventDelivery.objects.get(
        webhook_id=checkout_updated_webhook.id
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": checkout_update_delivery.id},
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 3
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_updated_webhook.id
    ).exists()

    shipping_methods_call, filter_shipping_call, tax_delivery_call = (
        mocked_send_webhook_request_sync.mock_calls
    )
    shipping_methods_delivery = shipping_methods_call.args[0]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id
    assert (
        shipping_methods_delivery.event_type
        == WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    )
    assert shipping_methods_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id
