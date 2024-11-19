import datetime
from decimal import Decimal
from unittest.mock import ANY, patch

import before_after
import graphene
import pytest
from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models.aggregates import Sum
from django.utils import timezone

from .....account.models import Address
from .....checkout import calculations
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout, CheckoutLine
from .....core.exceptions import InsufficientStock, InsufficientStockData
from .....core.taxes import TaxError, zero_money, zero_taxed_money
from .....discount import DiscountType, DiscountValueType, RewardValueType
from .....discount.models import CheckoutLineDiscount, Promotion
from .....giftcard import GiftCardEvents
from .....giftcard.models import GiftCard, GiftCardEvent
from .....order import OrderOrigin, OrderStatus
from .....order.models import Fulfillment, Order
from .....payment import ChargeStatus, PaymentError, TransactionKind
from .....payment.error_codes import PaymentErrorCode
from .....payment.gateways.dummy_credit_card import TOKEN_VALIDATION_MAPPING
from .....payment.interface import GatewayResponse
from .....payment.model_helpers import get_subtotal
from .....plugins.manager import PluginsManager, get_plugins_manager
from .....product.models import ProductChannelListing, ProductVariantChannelListing
from .....warehouse.models import Reservation, Stock, WarehouseClickAndCollectOption
from .....warehouse.tests.utils import get_available_quantity_for_stock
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_CHECKOUT_COMPLETE = """
    mutation checkoutComplete(
            $id: ID,
            $redirectUrl: String,
            $metadata: [MetadataInput!],
        ) {
        checkoutComplete(
                id: $id,
                redirectUrl: $redirectUrl,
                metadata: $metadata,
            ) {
            order {
                id
                token
                original
                origin
                deliveryMethod {
                    ... on Warehouse {
                        id
                    }
                    ... on ShippingMethod {
                        id
                    }
                }
                total {
                    currency
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
                subtotal {
                    currency
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
                undiscountedTotal {
                    currency
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
            }
            errors {
                field,
                message,
                variants,
                code
            }
            confirmationNeeded
            confirmationData
        }
    }
    """


def test_checkout_complete_with_inactive_channel(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    channel = checkout.channel
    channel.is_active = False
    channel.save()
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.calculate_checkout_total_with_gift_cards(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.CHANNEL_INACTIVE.name
    assert data["errors"][0]["field"] == "channel"
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


@pytest.mark.integration
@patch("saleor.order.calculations._recalculate_with_plugins")
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete(
    order_confirmed_mock,
    recalculate_with_plugins_mock,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
    caplog,
):
    # given
    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.tax_exemption = True
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    shipping_price = checkout.shipping_method.channel_listings.get(
        channel=checkout.channel
    ).price

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT
    assert not order.original
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert str(order.id) == order_token
    assert order.redirect_url == redirect_url
    assert order.total.gross == total.gross
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata
    assert order.total_charged_amount == payment.total
    assert order.total_authorized == zero_money(order.currency)

    order_line = order.lines.first()
    line_tax_class = order_line.tax_class
    shipping_tax_class = shipping_method.tax_class

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant

    assert order_line.tax_class == line_tax_class
    assert order_line.tax_class_name == line_tax_class.name
    assert order_line.tax_class_metadata == line_tax_class.metadata
    assert order_line.tax_class_private_metadata == line_tax_class.private_metadata

    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.shipping_tax_rate is not None
    assert order.shipping_tax_class_name == shipping_tax_class.name
    assert order.shipping_tax_class_metadata == shipping_tax_class.metadata
    assert (
        order.shipping_tax_class_private_metadata == shipping_tax_class.private_metadata
    )
    assert order.shipping_price_gross_amount == shipping_price.amount
    assert order.base_shipping_price_amount == shipping_price.amount
    assert order.undiscounted_base_shipping_price_amount == shipping_price.amount
    assert order.payments.exists()
    assert order.search_vector
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )
    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"
    order_confirmed_mock.assert_called_once_with(order, webhooks=set())
    recalculate_with_plugins_mock.assert_not_called()

    assert not len(Reservation.objects.all())

    assert (
        graphene.Node.to_global_id("Checkout", checkout_info.checkout.pk)
        == caplog.records[0].checkout_id
    )
    assert gift_card.initial_balance_amount == Decimal(
        caplog.records[0].gift_card_compensation
    )
    assert total.gross.amount == Decimal(
        caplog.records[0].total_after_gift_card_compensation
    )


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_with_metadata(
    order_confirmed_mock,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.metadata_storage.save()
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    redirect_url = "https://www.example.com"
    metadata_value = "metaValue"
    metadata_key = "metaKey"
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": redirect_url,
        "metadata": [{"key": metadata_key, "value": metadata_value}],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    # then
    assert not data["errors"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT
    assert not order.original

    assert order.metadata == {
        **checkout.metadata_storage.metadata,
        metadata_key: metadata_value,
    }
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"
    order_confirmed_mock.assert_called_once_with(order, webhooks=set())


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_with_metadata_updates_existing_keys(
    site_settings,
    user_api_client,
    checkout_with_item,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    meta_key = "testKey"
    new_meta_value = "newValue"
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={meta_key: "oldValue"})
    checkout.save()
    checkout.metadata_storage.save()

    assert checkout.metadata_storage.metadata[meta_key] != new_meta_value

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    redirect_url = "https://www.example.com"
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": redirect_url,
        "metadata": [{"key": meta_key, "value": new_meta_value}],
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_COMPLETE,
        variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    # then
    assert not data["errors"]
    order = Order.objects.first()
    assert order.metadata == {meta_key: new_meta_value}


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_with_metadata_checkout_without_metadata(
    order_confirmed_mock,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    # delete the current metadata
    checkout.metadata_storage.delete()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    redirect_url = "https://www.example.com"
    metadata_value = "metaValue"
    metadata_key = "metaKey"
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": redirect_url,
        "metadata": [{"key": metadata_key, "value": metadata_value}],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    # then
    assert not data["errors"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT
    assert not order.original

    assert order.metadata == {
        **checkout.metadata_storage.metadata,
        metadata_key: metadata_value,
    }
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"
    order_confirmed_mock.assert_called_once_with(order, webhooks=set())


@pytest.mark.integration
@patch("saleor.graphql.checkout.mutations.checkout_complete.complete_checkout")
def test_checkout_complete_by_app(
    mocked_complete_checkout,
    app_api_client,
    checkout_with_item,
    customer_user,
    permission_impersonate_user,
    payment_dummy,
    address,
    shipping_method,
):
    mocked_complete_checkout.return_value = (None, True, {})
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_COMPLETE,
        variables,
        permissions=[permission_impersonate_user],
        check_no_permissions=False,
    )

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert not data["errors"]

    mocked_complete_checkout.assert_called_once_with(
        checkout_info=ANY,
        lines=ANY,
        manager=ANY,
        payment_data=ANY,
        store_source=ANY,
        user=checkout.user,
        app=ANY,
        site_settings=ANY,
        redirect_url=ANY,
        metadata_list=ANY,
    )


@pytest.mark.integration
@patch("saleor.graphql.checkout.mutations.checkout_complete.complete_checkout")
def test_checkout_complete_by_app_with_missing_permission(
    mocked_complete_checkout,
    app_api_client,
    checkout_with_item,
    customer_user,
    permission_manage_users,
    payment_dummy,
    address,
    shipping_method,
):
    mocked_complete_checkout.return_value = (None, True, {})
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_COMPLETE,
        variables,
        permissions=[permission_manage_users],
        check_no_permissions=False,
    )

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert not data["errors"]

    mocked_complete_checkout.assert_called_once_with(
        checkout_info=ANY,
        lines=ANY,
        manager=ANY,
        payment_data=ANY,
        store_source=ANY,
        user=None,
        app=ANY,
        site_settings=ANY,
        redirect_url=ANY,
        metadata_list=ANY,
    )


@patch("saleor.giftcard.utils.send_gift_card_notification")
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_gift_card_bought(
    order_confirmed_mock,
    send_notification_mock,
    site_settings,
    customer_user,
    user_api_client,
    checkout_with_gift_card_items,
    address,
    shipping_method,
    payment_txn_captured,
):
    # given
    checkout = checkout_with_gift_card_items
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.user = customer_user
    checkout.save()
    checkout.metadata_storage.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.automatically_fulfill_non_shippable_gift_card = True
    channel.save()

    payment = payment_txn_captured
    payment.is_active = True
    payment.order = None
    payment.captured_amount = total.gross.amount
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    orders_count = Order.objects.count()
    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.status == OrderStatus.PARTIALLY_FULFILLED

    gift_card = GiftCard.objects.get()
    assert GiftCardEvent.objects.filter(gift_card=gift_card, type=GiftCardEvents.BOUGHT)
    send_notification_mock.assert_called_once_with(
        customer_user,
        None,
        customer_user,
        customer_user.email,
        gift_card,
        ANY,
        checkout.channel.slug,
        resending=False,
    )
    order_confirmed_mock.assert_called_once_with(order, webhooks=set())
    assert Fulfillment.objects.count() == 1


def test_checkout_complete_with_variant_without_sku(
    site_settings,
    user_api_client,
    checkout_with_item,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    checkout_line_variant.sku = None
    checkout_line_variant.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_id = graphene.Node.from_global_id(data["order"]["id"])[1]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.get(id=order_id)
    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT

    order_line = order.lines.first()
    assert order_line.product_sku is None
    assert order_line.product_variant_id == order_line.variant.get_global_id()


def test_checkout_complete_with_variant_without_price(
    site_settings,
    user_api_client,
    checkout_with_item,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    checkout_line_variant.channel_listings.filter(channel=checkout.channel).update(
        price_amount=None
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", checkout_line_variant.pk)
    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    errors = content["data"]["checkoutComplete"]["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [variant_id]
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_checkout_complete_with_line_without_channel_listing(
    channel_listing_model,
    listing_filter_field,
    site_settings,
    user_api_client,
    checkout_with_item,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id,
        **{listing_filter_field: checkout_line.variant_id},
    ).delete()

    variant_id = graphene.Node.to_global_id("ProductVariant", checkout_line_variant.pk)
    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    errors = content["data"]["checkoutComplete"]["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [variant_id]
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


@patch("saleor.order.calculations._recalculate_with_plugins")
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_requires_confirmation(
    order_confirmed_mock,
    recalculate_with_plugins_mock,
    user_api_client,
    site_settings,
    payment_dummy,
    checkout_ready_to_complete,
):
    channel = checkout_ready_to_complete.channel
    channel.automatically_confirm_all_new_orders = False
    channel.save()
    Site.objects.clear_cache()
    payment = payment_dummy
    payment.checkout = checkout_ready_to_complete
    payment.save()

    variables = {
        "id": to_global_id_or_none(checkout_ready_to_complete),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)

    order_id = graphene.Node.from_global_id(
        content["data"]["checkoutComplete"]["order"]["id"]
    )[1]
    order = Order.objects.get(pk=order_id)
    assert order.is_unconfirmed()
    order_confirmed_mock.assert_not_called()
    recalculate_with_plugins_mock.assert_not_called()


@pytest.mark.integration
def test_checkout_with_voucher_complete(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    code = voucher_percentage.codes.first()
    voucher_used_count = code.used
    voucher_percentage.usage_limit = voucher_used_count + 1
    voucher_percentage.save(update_fields=["usage_limit"])

    checkout = checkout_with_voucher_percentage
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    discount_amount = checkout.discount

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.total == total
    assert order.undiscounted_total == total + discount_amount

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1
    assert (
        order_line.unit_discount_amount
        == (discount_amount / checkout_line_quantity).amount
    )
    assert order_line.unit_discount_reason

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    order_discount = order.discounts.filter(type=DiscountType.VOUCHER).first()
    assert order_discount
    assert (
        order_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
    )
    assert order.voucher == voucher_percentage
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@pytest.mark.integration
def test_checkout_complete_with_voucher_apply_once_per_order(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    code = voucher_percentage.codes.first()
    voucher_used_count = code.used
    voucher_percentage.usage_limit = voucher_used_count + 1
    voucher_percentage.apply_once_per_order = True
    voucher_percentage.save(update_fields=["apply_once_per_order", "usage_limit"])

    checkout = checkout_with_voucher_percentage

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    discount_amount = checkout_line_variant.channel_listings.get(
        channel=checkout.channel
    ).price * (
        voucher_percentage.channel_listings.get(channel=checkout.channel).discount_value
        / 100
    )
    checkout.discount = discount_amount
    checkout.save()
    checkout.metadata_storage.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    assert order.total == total
    assert order.undiscounted_total == total + discount_amount

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    order_discount = order.discounts.filter(type=DiscountType.VOUCHER).first()
    assert order_discount
    assert (
        order_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
    )
    assert order.voucher == voucher_percentage
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_checkout_with_voucher_complete_product_on_promotion(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    payment_dummy,
    address,
    shipping_method,
    catalogue_promotion_without_rules,
):
    # given
    code = voucher_percentage.codes.first()
    voucher_used_count = code.used
    voucher_percentage.usage_limit = voucher_used_count + 1
    voucher_percentage.save(update_fields=["usage_limit"])

    checkout = checkout_with_voucher_percentage
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant
    channel = checkout.channel

    reward_value = Decimal("5")
    rule = catalogue_promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [
                    graphene.Node.to_global_id(
                        "Product", checkout_line_variant.product.id
                    )
                ]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel)

    variant_channel_listing = checkout_line_variant.channel_listings.get(
        channel=channel
    )

    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price_amount - reward_value
    )
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel.currency_code,
    )
    CheckoutLineDiscount.objects.create(
        line=checkout_line,
        type=DiscountType.PROMOTION,
        value_type=DiscountValueType.FIXED,
        amount_value=reward_value,
        currency=channel.currency_code,
        promotion_rule=rule,
    )

    catalogue_promotion_without_rules.name = ""
    catalogue_promotion_without_rules.save(update_fields=["name"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.total == total
    assert order.undiscounted_total == total + (
        order_line.undiscounted_total_price - order_line.total_price
    )
    assert order_line.discounts.count() == 1
    line_discount = order_line.discounts.first()
    assert line_discount.promotion_rule == rule
    assert line_discount.value_type == DiscountValueType.FIXED
    assert line_discount.amount_value == reward_value * order_line.quantity
    assert order_line.sale_id == graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.id
    )
    assert order_line.unit_discount_reason == (
        f"Entire order voucher code: {code.code} & Promotion: {order_line.sale_id}"
    )

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    assert order.voucher == voucher_percentage
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_checkout_with_voucher_on_specific_product_complete(
    user_api_client,
    checkout_with_item_and_voucher_specific_products,
    voucher_specific_product_type,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    code = voucher_specific_product_type.codes.first()
    voucher_used_count = code.used
    voucher_specific_product_type.usage_limit = voucher_used_count + 1
    voucher_specific_product_type.save(update_fields=["usage_limit"])

    checkout = checkout_with_item_and_voucher_specific_products
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.total == total
    assert order.undiscounted_total == total + (
        order_line.undiscounted_total_price - order_line.total_price
    )

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    order_discount = order.discounts.filter(type=DiscountType.VOUCHER).first()
    assert order_discount
    assert (
        order_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
    )

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    assert order.voucher == voucher_specific_product_type
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@pytest.mark.integration
def test_checkout_complete_with_voucher_single_use(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    code = voucher_percentage.codes.first()
    voucher_percentage.single_use = True
    voucher_percentage.save(update_fields=["single_use"])

    assert code.is_active

    checkout = checkout_with_voucher_percentage
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    discount_amount = checkout.discount

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.total == total
    assert order.undiscounted_total == total + discount_amount

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    code.refresh_from_db()
    order_discount = order.discounts.filter(type=DiscountType.VOUCHER).first()
    assert order_discount
    assert (
        order_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
    )

    code.refresh_from_db()
    assert not code.is_active
    assert order.voucher == voucher_percentage
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@pytest.mark.integration
def test_checkout_complete_with_voucher_and_gift_card(
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    checkout_with_voucher_percentage.gift_cards.add(gift_card)
    code = voucher_percentage.codes.first()
    voucher_used_count = code.used
    voucher_percentage.usage_limit = voucher_used_count + 1
    voucher_percentage.save(update_fields=["usage_limit"])

    checkout = checkout_with_voucher_percentage
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    discount_amount = checkout.discount

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    gift_card_initial_balance = gift_card.initial_balance_amount
    shipping_price = shipping_method.channel_listings.get(
        channel=checkout.channel
    ).price

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.total == total
    assert order.undiscounted_total == subtotal + shipping_price + discount_amount

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1
    assert (
        order_line.unit_discount_amount
        == (discount_amount / checkout_line_quantity).amount
    )
    assert order_line.unit_discount_reason

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    order_discount = order.discounts.filter(type=DiscountType.VOUCHER).first()
    assert order_discount
    assert (
        order_discount.amount_value
        == (order.undiscounted_total - order.total).gross.amount
        - gift_card_initial_balance
    )
    assert order.voucher == voucher_percentage
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )


@pytest.mark.integration
def test_checkout_complete_free_shipping_voucher_and_gift_card(
    user_api_client,
    checkout_with_voucher_free_shipping,
    voucher_free_shipping,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_voucher_free_shipping
    shipping_listing = shipping_method.channel_listings.get(
        channel_id=checkout.channel_id
    )
    shipping_listing.price_amount = Decimal("35")
    shipping_listing.save(update_fields=["price_amount"])

    checkout.gift_cards.add(gift_card)

    code = voucher_free_shipping.codes.first()
    voucher_used_count = code.used
    voucher_free_shipping.usage_limit = voucher_used_count + 1
    voucher_free_shipping.save(update_fields=["usage_limit"])

    checkout.discount = shipping_listing.price
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    shipping_price = shipping_method.channel_listings.get(
        channel=checkout.channel
    ).price

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.total == total
    assert order.shipping_price == zero_taxed_money(order.currency)
    assert order.undiscounted_total == subtotal + shipping_price

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1
    assert order_line.unit_discount_amount == 0

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    order_discount = order.discounts.filter(type=DiscountType.VOUCHER).first()
    assert order_discount
    assert order_discount.amount_value == shipping_price.amount
    assert order.voucher == voucher_free_shipping
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )


def test_checkout_complete_product_on_promotion(
    user_api_client,
    checkout_with_item,
    catalogue_promotion_without_rules,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    channel = checkout.channel

    reward_value = Decimal("5")
    rule = catalogue_promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [
                    graphene.Node.to_global_id(
                        "Product", checkout_line_variant.product.id
                    )
                ]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel)

    variant_channel_listing = checkout_line_variant.channel_listings.get(
        channel=channel
    )

    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price_amount - reward_value
    )
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel.currency_code,
    )
    CheckoutLineDiscount.objects.create(
        line=checkout_line,
        type=DiscountType.PROMOTION,
        value_type=DiscountValueType.FIXED,
        amount_value=reward_value,
        currency=channel.currency_code,
        promotion_rule=rule,
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.total == total
    assert order.undiscounted_total == total + (
        order_line.undiscounted_total_price - order_line.total_price
    )

    assert order_line.discounts.count() == 1
    line_discount = order_line.discounts.first()
    assert line_discount.promotion_rule == rule
    assert line_discount.value_type == DiscountValueType.FIXED
    assert line_discount.amount_value == reward_value * order_line.quantity

    assert order_line.sale_id == graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.id
    )
    assert order_line.unit_discount_reason == f"Promotion: {order_line.sale_id}"

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order_line.is_price_overridden is False
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_checkout_complete_product_on_promotion_deleted_promotion_instance(
    user_api_client,
    checkout_with_item,
    catalogue_promotion_without_rules,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    channel = checkout.channel
    reward_value = Decimal("5")
    rule = catalogue_promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [
                    graphene.Node.to_global_id(
                        "Product", checkout_line_variant.product.id
                    )
                ]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel)
    promotion_id = graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.id
    )

    variant_channel_listing = checkout_line_variant.channel_listings.get(
        channel=channel
    )

    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price_amount - reward_value
    )
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel.currency_code,
    )
    CheckoutLineDiscount.objects.create(
        line=checkout_line,
        type=DiscountType.PROMOTION,
        value_type=DiscountValueType.FIXED,
        amount_value=reward_value,
        currency=channel.currency_code,
        promotion_rule=rule,
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    checkout_id = to_global_id_or_none(checkout)
    variables = {
        "id": checkout_id,
        "redirectUrl": "https://www.example.com",
    }

    def delete_promotion(*args, **kwargs):
        Promotion.objects.get(id=catalogue_promotion_without_rules.id).delete()

    # when
    with before_after.before(
        "saleor.checkout.complete_checkout.complete_checkout_with_payment",
        delete_promotion,
    ):
        response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    assert order.total == total
    assert order.undiscounted_total == total + (
        order_line.undiscounted_total_price - order_line.total_price
    )
    assert not order_line.sale_id
    assert order_line.unit_discount_reason
    assert order_line.unit_discount_reason == f"Promotion: {promotion_id}"
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant

    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_checkout_complete_price_override(
    user_api_client,
    checkout_with_item,
    catalogue_promotion_without_rules,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.tax_exemption = True
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line.price_override = Decimal("2.0")
    checkout_line.save(update_fields=["price_override"])

    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    assert order.total == total
    assert order.undiscounted_total == total + (
        order_line.undiscounted_total_price - order_line.total_price
    )

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order_line.is_price_overridden is True
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1
    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_checkout_complete_product_on_old_sale(
    user_api_client,
    checkout_with_item,
    catalogue_promotion_without_rules,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    channel = checkout.channel

    old_sale_id = 1
    catalogue_promotion_without_rules.old_sale_id = old_sale_id
    catalogue_promotion_without_rules.save(update_fields=["old_sale_id"])

    reward_value = Decimal("5")
    rule = catalogue_promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [
                    graphene.Node.to_global_id(
                        "Product", checkout_line_variant.product.id
                    )
                ]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel)

    variant_channel_listing = checkout_line_variant.channel_listings.get(
        channel=channel
    )

    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price_amount - reward_value
    )
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel.currency_code,
    )
    CheckoutLineDiscount.objects.create(
        line=checkout_line,
        type=DiscountType.PROMOTION,
        value_type=DiscountValueType.FIXED,
        amount_value=reward_value,
        currency=channel.currency_code,
        promotion_rule=rule,
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.total == total
    assert order.undiscounted_total == total + (
        order_line.undiscounted_total_price - order_line.total_price
    )

    assert order_line.discounts.count() == 1
    line_discount = order_line.discounts.first()
    assert line_discount.promotion_rule == rule
    assert line_discount.value_type == DiscountValueType.FIXED
    assert line_discount.amount_value == reward_value * order_line.quantity

    assert order_line.sale_id == graphene.Node.to_global_id(
        "Sale", catalogue_promotion_without_rules.old_sale_id
    )
    assert order_line.unit_discount_reason == f"Sale: {order_line.sale_id}"

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_checkout_with_voucher_on_specific_product_complete_with_product_on_promotion(
    user_api_client,
    checkout_with_item_and_voucher_specific_products,
    voucher_specific_product_type,
    catalogue_promotion_without_rules,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    code = voucher_specific_product_type.codes.first()
    voucher_used_count = code.used
    voucher_specific_product_type.usage_limit = voucher_used_count + 1
    voucher_specific_product_type.save(update_fields=["usage_limit"])

    checkout = checkout_with_item_and_voucher_specific_products
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    channel = checkout.channel

    reward_value = Decimal("5")
    rule = catalogue_promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [
                    graphene.Node.to_global_id(
                        "Product", checkout_line_variant.product.id
                    )
                ]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel)

    variant_channel_listing = checkout_line_variant.channel_listings.get(
        channel=channel
    )

    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price_amount - reward_value
    )
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel.currency_code,
    )
    line_discount = CheckoutLineDiscount.objects.create(
        line=checkout_line,
        type=DiscountType.PROMOTION,
        value_type=DiscountValueType.FIXED,
        amount_value=reward_value,
        currency=channel.currency_code,
        promotion_rule=rule,
        name=catalogue_promotion_without_rules.name,
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.total == total
    assert order.undiscounted_total == total + (
        order_line.undiscounted_total_price - order_line.total_price
    )

    assert order_line.discounts.count() == 1
    line_discount = order_line.discounts.first()
    assert line_discount.promotion_rule == rule
    assert line_discount.value_type == DiscountValueType.FIXED
    assert line_discount.amount_value == reward_value * order_line.quantity

    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order_line.sale_id == graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.id
    )
    unit_discount_reason = (
        f"Voucher code: {voucher_specific_product_type.code}"
        f" & Promotion: {order_line.sale_id}"
    )
    assert order_line.unit_discount_reason == unit_discount_reason
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    code.refresh_from_db()
    assert code.used == voucher_used_count + 1
    assert order.voucher == voucher_specific_product_type
    assert order.voucher.code == code.code

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@patch.object(PluginsManager, "preprocess_order_creation")
@pytest.mark.integration
def test_checkout_with_voucher_not_increase_uses_on_preprocess_order_creation_failure(
    mocked_preprocess_order_creation,
    user_api_client,
    checkout_with_voucher_percentage,
    voucher_percentage,
    payment_dummy,
    address,
    shipping_method,
):
    code = voucher_percentage.codes.first()
    mocked_preprocess_order_creation.side_effect = TaxError("tax error!")
    code.used = 0
    voucher_percentage.usage_limit = 1
    voucher_percentage.save(update_fields=["usage_limit"])
    code.save(update_fields=["used"])

    checkout = checkout_with_voucher_percentage
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert data["errors"][0]["code"] == CheckoutErrorCode.TAX_ERROR.name

    code.refresh_from_db()
    assert code.used == 0

    assert Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout shouldn't have been deleted"
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


@pytest.mark.integration
def test_checkout_complete_without_inventory_tracking(
    user_api_client,
    checkout_with_variant_without_inventory_tracking,
    payment_dummy,
    address,
    shipping_method,
):
    checkout = checkout_with_variant_without_inventory_tracking
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert not order_line.allocations.all()
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_checkout_complete_checkout_without_lines(
    site_settings,
    user_api_client,
    checkout,
    payment_dummy,
    address,
    shipping_method,
):
    checkout = checkout
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    assert not lines
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == CheckoutErrorCode.NO_LINES.name
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


@pytest.mark.integration
@pytest.mark.parametrize(("token", "error"), list(TOKEN_VALIDATION_MAPPING.items()))
@patch(
    "saleor.payment.gateways.dummy_credit_card.plugin."
    "DummyCreditCardGatewayPlugin.DEFAULT_ACTIVE",
    True,
)
def test_checkout_complete_error_in_gateway_response_for_dummy_credit_card(
    token,
    error,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy_credit_card,
    address,
    shipping_method,
):
    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    payment = payment_dummy_credit_card
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.token = token
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"])
    assert data["errors"][0]["message"] == error
    assert payment.transactions.count() == 1
    assert Order.objects.count() == orders_count
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


ERROR_GATEWAY_RESPONSE = GatewayResponse(
    is_success=False,
    action_required=False,
    kind=TransactionKind.CAPTURE,
    amount=Decimal(0),
    currency="usd",
    transaction_id="1234",
    error="ERROR",
)


def _process_payment_transaction_returns_error(*args, **kwards):
    return ERROR_GATEWAY_RESPONSE


def _process_payment_raise_error(*args, **kwargs):
    raise PaymentError("Oops! Something went wrong.")


@pytest.fixture(
    params=[_process_payment_raise_error, _process_payment_transaction_returns_error]
)
def error_side_effect(request):
    return request.param


@patch.object(PluginsManager, "process_payment")
def test_checkout_complete_does_not_delete_checkout_after_unsuccessful_payment(
    mocked_process_payment,
    error_side_effect,
    user_api_client,
    checkout_with_voucher,
    voucher,
    payment_dummy,
    address,
    shipping_method,
):
    mocked_process_payment.side_effect = error_side_effect
    code = voucher.codes.first()
    expected_voucher_usage_count = code.used
    checkout = checkout_with_voucher
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    taxed_total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = taxed_total.gross.amount
    payment.currency = taxed_total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    get_graphql_content(response)

    assert Order.objects.count() == orders_count

    payment.refresh_from_db(fields=["order"])
    transaction = payment.transactions.get()
    assert transaction.error
    assert payment.order is None

    # ensure the voucher usage count was not incremented
    code.refresh_from_db(fields=["used"])
    assert code.used == expected_voucher_usage_count

    assert Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should not have been deleted"
    checkout.refresh_from_db()
    assert not checkout.completing_started_at

    mocked_process_payment.assert_called_once()


def test_checkout_complete_invalid_id(user_api_client):
    id = "12345"
    variables = {"id": id, "redirectUrl": "https://www.example.com"}
    orders_count = Order.objects.count()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"][0]["message"] == f"Invalid ID: {id}. Expected: Checkout."
    assert data["errors"][0]["field"] == "id"
    assert orders_count == Order.objects.count()


def test_checkout_complete_no_payment(
    user_api_client, checkout_with_item, address, shipping_method
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    orders_count = Order.objects.count()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"][0]["message"] == (
        "Provided payment methods can not cover the checkout's total amount"
    )
    assert orders_count == Order.objects.count()
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


@patch.object(PluginsManager, "process_payment")
def test_checkout_complete_confirmation_needed(
    mocked_process_payment,
    user_api_client,
    checkout_with_item,
    address,
    payment_dummy,
    shipping_method,
    action_required_gateway_response,
):
    # given
    mocked_process_payment.return_value = action_required_gateway_response

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    orders_count = Order.objects.count()

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]
    assert data["confirmationNeeded"] is True
    assert data["confirmationData"]

    new_orders_count = Order.objects.count()
    assert new_orders_count == orders_count
    checkout.refresh_from_db()
    payment_dummy.refresh_from_db()
    assert payment_dummy.is_active
    assert payment_dummy.to_confirm

    mocked_process_payment.assert_called_once()

    checkout.refresh_from_db()
    assert not checkout.completing_started_at


@patch.object(PluginsManager, "confirm_payment")
def test_checkout_confirm(
    mocked_confirm_payment,
    user_api_client,
    checkout_with_item,
    payment_txn_to_confirm,
    address,
    shipping_method,
    action_required_gateway_response,
):
    response = action_required_gateway_response
    response.action_required = False
    mocked_confirm_payment.return_value = response

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_txn_to_confirm
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    orders_count = Order.objects.count()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert not data["errors"]
    assert not data["confirmationNeeded"]

    mocked_confirm_payment.assert_called_once()

    new_orders_count = Order.objects.count()
    assert new_orders_count == orders_count + 1


def test_checkout_complete_insufficient_stock(
    user_api_client, checkout_with_item, address, payment_dummy, shipping_method
):
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    orders_count = Order.objects.count()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"][0]["message"] == "Insufficient product stock: 123"
    assert orders_count == Order.objects.count()

    checkout.refresh_from_db()
    assert not checkout.completing_started_at


@patch("saleor.checkout.complete_checkout.gateway.refund")
def test_checkout_complete_insufficient_stock_payment_refunded(
    gateway_refund_mock,
    checkout_with_item,
    address,
    shipping_method,
    payment_dummy,
    user_api_client,
):
    # given
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()

    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    orders_count = Order.objects.count()

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert data["errors"][0]["message"] == "Insufficient product stock: 123"
    assert orders_count == Order.objects.count()

    gateway_refund_mock.assert_called_once_with(
        payment, ANY, channel_slug=checkout_info.channel.slug
    )

    checkout.refresh_from_db()
    assert not checkout.completing_started_at


@patch("saleor.checkout.complete_checkout.gateway.void")
def test_checkout_complete_insufficient_stock_payment_voided(
    gateway_void_mock,
    checkout_with_item,
    address,
    shipping_method,
    payment_txn_preauth,
    user_api_client,
):
    # given
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()

    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    payment = payment_txn_preauth
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.charge_status = ChargeStatus.NOT_CHARGED
    payment.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    orders_count = Order.objects.count()

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert data["errors"][0]["message"] == "Insufficient product stock: 123"
    assert orders_count == Order.objects.count()

    gateway_void_mock.assert_called_once_with(
        payment, ANY, channel_slug=checkout_info.channel.slug
    )

    checkout.refresh_from_db()
    assert not checkout.completing_started_at


def test_checkout_complete_insufficient_stock_reserved_by_other_user(
    site_settings_with_reservations,
    user_api_client,
    checkout_with_item,
    address,
    payment_dummy,
    shipping_method,
    channel_USD,
):
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)

    other_checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    other_checkout_line = other_checkout.lines.create(
        variant=checkout_line.variant,
        quantity=quantity_available,
        undiscounted_unit_price_amount=checkout_line.variant.channel_listings.get(
            channel=channel_USD
        ).price_amount,
    )
    Reservation.objects.create(
        checkout_line=other_checkout_line,
        stock=stock,
        quantity_reserved=quantity_available,
        reserved_until=timezone.now() + datetime.timedelta(minutes=5),
    )

    checkout_line.quantity = 1
    checkout_line.save()
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    orders_count = Order.objects.count()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"][0]["message"] == "Insufficient product stock: 123"
    assert orders_count == Order.objects.count()
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


def test_checkout_complete_own_reservation(
    site_settings_with_reservations,
    user_api_client,
    checkout_with_item,
    address,
    payment_dummy,
    shipping_method,
    channel_USD,
):
    checkout = checkout_with_item
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)

    checkout_line.quantity = quantity_available
    checkout_line.save()
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    reservation = Reservation.objects.create(
        checkout_line=checkout_line,
        stock=stock,
        quantity_reserved=quantity_available,
        reserved_until=timezone.now() + datetime.timedelta(minutes=5),
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    orders_count = Order.objects.count()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)

    order_line = order.lines.first()
    assert order_line.quantity == quantity_available
    assert order_line.variant == checkout_line.variant

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"

    # Reservation associated with checkout has been deleted
    with pytest.raises(Reservation.DoesNotExist):
        reservation.refresh_from_db()


def test_checkout_complete_without_redirect_url(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {"id": to_global_id_or_none(checkout)}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.total.gross == total.gross

    order_line = order.lines.first()
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    gift_card.refresh_from_db()
    assert gift_card.current_balance == zero_money(gift_card.currency)
    assert gift_card.last_used_on

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


@patch("saleor.checkout.complete_checkout.gateway.payment_refund_or_void")
def test_checkout_complete_payment_payment_total_different_than_checkout(
    gateway_refund_or_void_mock,
    checkout_with_items,
    payment_dummy,
    user_api_client,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_items
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount - Decimal(10)
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert data["errors"][0]["code"] == CheckoutErrorCode.CHECKOUT_NOT_FULLY_PAID.name
    assert orders_count == Order.objects.count()
    checkout.refresh_from_db()
    assert not checkout.completing_started_at

    gateway_refund_or_void_mock.assert_called_with(
        payment, ANY, channel_slug=checkout_info.channel.slug
    )


def test_order_already_exists(
    user_api_client, checkout_ready_to_complete, payment_dummy, order_with_lines
):
    checkout = checkout_ready_to_complete
    order_with_lines.checkout_token = checkout.token
    order_with_lines.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    checkout.delete()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)

    assert Checkout.objects.count() == 0


@patch("saleor.checkout.complete_checkout._create_order")
def test_create_order_raises_insufficient_stock(
    mocked_create_order, user_api_client, checkout_ready_to_complete, payment_dummy
):
    checkout = checkout_ready_to_complete
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    mocked_create_order.side_effect = InsufficientStock(
        [InsufficientStockData(variant=lines[0].variant, available_quantity=0)]
    )
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, checkout.shipping_address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert mocked_create_order.called
    checkout.refresh_from_db()
    assert not checkout.completing_started_at

    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_REFUNDED


def test_checkout_complete_with_digital(
    api_client, checkout_with_digital_item, address, payment_dummy
):
    """Ensure it is possible to complete a digital checkout without shipping."""

    order_count = Order.objects.count()
    checkout = checkout_with_digital_item
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # Set a billing address
    checkout.billing_address = address
    checkout.save(update_fields=["billing_address"])

    # Create a dummy payment to charge
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    # Send the creation request
    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)["data"]["checkoutComplete"]
    assert not content["errors"]

    # Ensure the order was actually created
    assert (
        Order.objects.count() == order_count + 1
    ), "The order should have been created"


@pytest.mark.integration
def test_checkout_complete_0_total_value(
    user_api_client,
    checkout_with_item,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    assert not gift_card.last_used_on

    checkout = checkout_with_item
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_quantity = checkout_line.quantity
    checkout_line_variant = checkout_line.variant

    product_type = checkout_line_variant.product.product_type
    product_type.is_shipping_required = False
    product_type.save(update_fields=["is_shipping_required"])

    checkout_line_variant.cost_price_amount = Decimal(0)
    checkout_line_variant.price_amount = Decimal(0)
    checkout_line_variant.save()

    checkout.refresh_from_db()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.total.gross == total.gross
    assert order.metadata == checkout.metadata_storage.metadata
    assert order.private_metadata == checkout.metadata_storage.private_metadata

    order_line = order.lines.first()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert checkout_line_quantity == order_line.quantity
    assert checkout_line_variant == order_line.variant
    assert order.shipping_address is None
    assert order.shipping_method is None
    assert order.shipping_price_gross_amount == 0
    assert order.base_shipping_price_amount == 0
    assert order.undiscounted_base_shipping_price_amount == 0
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 1

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"


def test_complete_checkout_for_local_click_and_collect(
    api_client,
    checkout_with_item_for_cc,
    payment_dummy,
    address,
    warehouse_for_cc,
    warehouse,
):
    # given
    order_count = Order.objects.count()
    checkout = checkout_with_item_for_cc
    checkout.collection_point = warehouse_for_cc
    checkout.shipping_address = warehouse_for_cc.address
    checkout.save(update_fields=["collection_point", "shipping_address"])

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    assert not payment.transactions.exists()
    assert len(lines) == 1
    variant = lines[0].variant

    # create another stock for the variant with the bigger quantity available
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=15)

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)["data"]["checkoutComplete"]

    assert not content["errors"]
    assert Order.objects.count() == order_count + 1

    order = Order.objects.first()

    assert order.collection_point == warehouse_for_cc
    assert order.shipping_method is None
    assert order.shipping_address
    assert order.shipping_address.id != warehouse_for_cc.address.id
    assert order.shipping_price == zero_taxed_money(payment.currency)
    assert order.lines.count() == 1

    # ensure the allocation is made on the correct warehouse
    assert order.lines.first().allocations.first().stock.warehouse == warehouse_for_cc


def test_complete_checkout_for_global_click_and_collect(
    api_client,
    checkout_with_item_for_cc,
    payment_dummy,
    address,
    warehouse_for_cc,
    warehouse,
):
    """Test that click-and-collect prefers the local stock even if other warehouses hold more stock."""
    # given
    order_count = Order.objects.count()
    checkout = checkout_with_item_for_cc

    warehouse_for_cc.click_and_collect_option = (
        WarehouseClickAndCollectOption.ALL_WAREHOUSES
    )
    warehouse_for_cc.save(update_fields=["click_and_collect_option"])

    checkout.collection_point = warehouse_for_cc
    checkout.save(update_fields=["collection_point"])

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    assert not payment.transactions.exists()
    assert len(lines) == 1
    variant = lines[0].variant

    # create another stock for the variant with the bigger quantity available
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=50)

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)["data"]["checkoutComplete"]

    assert not content["errors"]
    assert Order.objects.count() == order_count + 1

    order = Order.objects.latest("created_at")

    assert order.collection_point == warehouse_for_cc
    assert order.shipping_method is None
    assert order.shipping_address
    assert order.shipping_address.id != warehouse_for_cc.address.id
    assert order.shipping_price == zero_taxed_money(payment.currency)
    assert order.lines.count() == 1

    # ensure the allocation is made on the correct warehouse
    assert order.lines.first().allocations.first().stock.warehouse == warehouse_for_cc


def test_complete_checkout_raises_error_for_local_stock(
    api_client, checkout_with_item_for_cc, payment_dummy, address, warehouse_for_cc
):
    initial_order_count = Order.objects.count()
    checkout = checkout_with_item_for_cc
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(product_variant=checkout_line.variant)
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "rediirectUrl": "https://www.example.com",
    }

    checkout.collection_point = warehouse_for_cc
    checkout.billing_address = address
    checkout.save(
        update_fields=["collection_point", "shipping_address", "billing_address"]
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = Decimal("20")
    payment.currency = checkout.currency
    payment.checkout = checkout
    payment.save()

    assert not payment.transactions.exists()

    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)["data"]["checkoutComplete"]
    assert content["errors"][0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert Order.objects.count() == initial_order_count


def test_comp_checkout_builds_order_for_all_warehouse_even_if_not_available_locally(
    stocks_for_cc,
    warehouse_for_cc,
    checkout_with_item_for_cc,
    address,
    api_client,
    payment_dummy,
):
    initial_order_count = Order.objects.count()
    checkout = checkout_with_item_for_cc
    checkout_line = checkout.lines.first()
    stock = Stock.objects.get(
        product_variant=checkout_line.variant, warehouse=warehouse_for_cc
    )
    quantity_available = get_available_quantity_for_stock(stock)
    checkout_line.quantity = quantity_available + 1
    checkout_line.save()

    warehouse_for_cc.click_and_collect_option = (
        WarehouseClickAndCollectOption.ALL_WAREHOUSES
    )
    warehouse_for_cc.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "rediirectUrl": "https://www.example.com",
    }

    checkout.collection_point = warehouse_for_cc
    checkout.save(update_fields=["collection_point"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    assert not payment.transactions.exists()

    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)["data"]["checkoutComplete"]
    assert not content["errors"]
    assert Order.objects.count() == initial_order_count + 1


def test_checkout_complete_raises_InsufficientStock_when_quantity_above_stock_sum(
    stocks_for_cc,
    warehouse_for_cc,
    checkout_with_item_for_cc,
    address,
    api_client,
    payment_dummy,
):
    initial_order_count = Order.objects.count()
    checkout = checkout_with_item_for_cc
    checkout_line = checkout.lines.first()
    overall_stock_quantity = (
        Stock.objects.filter(product_variant=checkout_line.variant).aggregate(
            Sum("quantity")
        )
    ).pop("quantity__sum")
    checkout_line.quantity = overall_stock_quantity + 1
    checkout_line.save()
    warehouse_for_cc.click_and_collect_option = (
        WarehouseClickAndCollectOption.ALL_WAREHOUSES
    )
    warehouse_for_cc.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "rediirectUrl": "https://www.example.com",
    }

    checkout.collection_point = warehouse_for_cc
    checkout.billing_address = address
    checkout.save(update_fields=["collection_point", "billing_address"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    assert not payment.transactions.exists()

    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)["data"]["checkoutComplete"]
    assert content["errors"][0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert Order.objects.count() == initial_order_count


def test_checkout_complete_raises_InvalidShippingMethod_when_warehouse_disabled(
    warehouse_for_cc,
    checkout_with_item_for_cc,
    address,
    api_client,
    payment_dummy,
):
    initial_order_count = Order.objects.count()
    checkout = checkout_with_item_for_cc
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    checkout.billing_address = address
    checkout.collection_point = warehouse_for_cc

    checkout.save(
        update_fields=["shipping_address", "billing_address", "collection_point"]
    )

    warehouse_for_cc.click_and_collect_option = WarehouseClickAndCollectOption.DISABLED
    warehouse_for_cc.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    assert not checkout_info.valid_pick_up_points
    assert not checkout_info.delivery_method_info.is_method_in_valid_methods(
        checkout_info
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    assert not payment.transactions.exists()

    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)["data"]["checkoutComplete"]

    assert (
        content["errors"][0]["code"] == CheckoutErrorCode.INVALID_SHIPPING_METHOD.name
    )
    assert Order.objects.count() == initial_order_count
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.order_confirmed")
def test_checkout_complete_with_preorder_variant(
    order_confirmed_mock,
    site_settings,
    user_api_client,
    checkout_with_item_and_preorder_item,
    payment_dummy,
    address,
    shipping_method,
):
    checkout = checkout_with_item_and_preorder_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    variants_and_quantities = {line.variant_id: line.quantity for line in checkout}

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order_token = data["order"]["token"]
    order_id = data["order"]["id"]
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.status == OrderStatus.UNFULFILLED
    assert order.origin == OrderOrigin.CHECKOUT
    assert not order.original
    assert str(order.id) == order_token
    assert order_id == graphene.Node.to_global_id("Order", order.id)
    assert order.total.gross == total.gross

    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert order.subtotal == subtotal
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.lines.count() == len(variants_and_quantities)
    for variant_id, quantity in variants_and_quantities.items():
        assert order.lines.get(variant_id=variant_id).quantity == quantity
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    assert payment.transactions.count() == 1

    preorder_line = order.lines.filter(variant__is_preorder=True).first()
    assert not preorder_line.allocations.exists()
    preorder_allocation = preorder_line.preorder_allocations.get()
    assert preorder_allocation.quantity == quantity

    stock_line = order.lines.filter(variant__is_preorder=False).first()
    assert stock_line.allocations.exists()
    assert not stock_line.preorder_allocations.exists()

    assert not Checkout.objects.filter(
        pk=checkout.pk
    ).exists(), "Checkout should have been deleted"
    order_confirmed_mock.assert_called_once_with(order, webhooks=set())


def test_checkout_complete_with_click_collect_preorder_fails_for_disabled_warehouse(
    warehouse_for_cc,
    checkout_with_items_for_cc,
    address,
    api_client,
    payment_dummy,
):
    initial_order_count = Order.objects.count()
    checkout = checkout_with_items_for_cc
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    checkout.billing_address = address
    checkout.collection_point = warehouse_for_cc

    checkout_line = checkout.lines.first()
    checkout_line.variant.is_preorder = True
    checkout_line.variant.preorder_global_threshold = 100
    checkout_line.variant.save()

    for line in checkout.lines.all():
        if line.variant.channel_listings.filter(channel=checkout.channel).exists():
            continue

        line.variant.channel_listings.create(
            channel=checkout.channel,
            price_amount=Decimal(15),
            currency=checkout.currency,
        )

    checkout.save(
        update_fields=["shipping_address", "billing_address", "collection_point"]
    )

    warehouse_for_cc.click_and_collect_option = WarehouseClickAndCollectOption.DISABLED
    warehouse_for_cc.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    assert not checkout_info.valid_pick_up_points
    assert not checkout_info.delivery_method_info.is_method_in_valid_methods(
        checkout_info
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    assert not payment.transactions.exists()

    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)["data"]["checkoutComplete"]

    assert (
        content["errors"][0]["code"] == CheckoutErrorCode.INVALID_SHIPPING_METHOD.name
    )
    assert Order.objects.count() == initial_order_count
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


def test_checkout_complete_variant_channel_listing_does_not_exist(
    user_api_client,
    checkout_with_items,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_items
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    checkout_line_variant.channel_listings.get(channel__id=checkout.channel_id).delete()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)

    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [
        graphene.Node.to_global_id("ProductVariant", checkout_line_variant.pk)
    ]

    assert Order.objects.count() == orders_count
    assert Checkout.objects.filter(pk=checkout.pk).exists()
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


def test_checkout_complete_variant_channel_listing_no_price(
    user_api_client,
    checkout_with_items,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_items
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    variants = []
    for line in checkout.lines.all()[:2]:
        checkout_line_variant = line.variant
        variants.append(checkout_line_variant)
        variant_channel_listing = checkout_line_variant.channel_listings.get(
            channel__id=checkout.channel_id
        )
        variant_channel_listing.price_amount = None
        variant_channel_listing.save(update_fields=["price_amount"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"
    assert set(errors[0]["variants"]) == {
        graphene.Node.to_global_id("ProductVariant", variant.pk) for variant in variants
    }

    assert Order.objects.count() == orders_count
    assert Checkout.objects.filter(pk=checkout.pk).exists()
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


def test_checkout_complete_product_channel_listing_does_not_exist(
    user_api_client,
    checkout_with_items,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_items
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    checkout_line_variant.product.channel_listings.get(
        channel__id=checkout.channel_id
    ).delete()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [
        graphene.Node.to_global_id("ProductVariant", checkout_line_variant.pk)
    ]

    assert Order.objects.count() == orders_count
    assert Checkout.objects.filter(pk=checkout.pk).exists()
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


@pytest.mark.parametrize(
    "available_for_purchase",
    [None, datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=1)],
)
def test_checkout_complete_product_channel_listing_not_available_for_purchase(
    user_api_client,
    checkout_with_items,
    payment_dummy,
    address,
    shipping_method,
    available_for_purchase,
):
    # given
    checkout = checkout_with_items
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    checkout_line = checkout.lines.first()
    checkout_line_variant = checkout_line.variant
    product_channel_listings = checkout_line_variant.product.channel_listings.get(
        channel__id=checkout.channel_id
    )
    product_channel_listings.available_for_purchase_at = available_for_purchase
    product_channel_listings.save(update_fields=["available_for_purchase_at"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"
    assert errors[0]["variants"] == [
        graphene.Node.to_global_id("ProductVariant", checkout_line_variant.pk)
    ]

    assert Order.objects.count() == orders_count
    assert Checkout.objects.filter(pk=checkout.pk).exists()
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


def test_checkout_complete_error_when_shipping_address_doesnt_have_all_required_fields(
    user_api_client,
    checkout_with_item,
    gift_card,
    payment_dummy_credit_card,
    address,
    shipping_method,
):
    # given
    shipping_address = Address.objects.create(
        first_name="John",
        last_name="Doe",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        country="PL",
        phone="+48713988102",
    )  # missing postalCode

    checkout = checkout_with_item
    checkout.shipping_address = shipping_address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    payment = payment_dummy_credit_card
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.token = "123"
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1

    assert data["errors"][0]["code"] == "REQUIRED"
    assert data["errors"][0]["field"] == "postalCode"
    assert Order.objects.count() == orders_count
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


def test_checkout_complete_error_when_shipping_address_doesnt_have_all_valid_fields(
    user_api_client,
    checkout_with_item,
    gift_card,
    payment_dummy_credit_card,
    address,
    shipping_method,
):
    # given
    shipping_address = Address.objects.create(
        first_name="John",
        last_name="Doe",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        country="PL",
        phone="+48713988102",
        postal_code="XX-ABC",
    )  # incorrect postalCode

    checkout = checkout_with_item
    checkout.shipping_address = shipping_address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    payment = payment_dummy_credit_card
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.token = "123"
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1

    assert data["errors"][0]["code"] == "INVALID"
    assert data["errors"][0]["field"] == "postalCode"
    assert Order.objects.count() == orders_count
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


def test_checkout_complete_error_when_billing_address_doesnt_have_all_required_fields(
    user_api_client,
    checkout_with_item,
    gift_card,
    payment_dummy_credit_card,
    address,
    shipping_method,
):
    # given
    billing_address = Address.objects.create(
        first_name="John",
        last_name="Doe",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        country="PL",
        phone="+48713988102",
    )  # missing postalCode

    checkout = checkout_with_item
    checkout.billing_address = billing_address
    checkout.shipping_method = shipping_method
    checkout.shipping_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    payment = payment_dummy_credit_card
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.token = "123"
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == "REQUIRED"
    assert data["errors"][0]["field"] == "postalCode"
    assert Order.objects.count() == orders_count
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


def test_checkout_complete_error_when_billing_address_doesnt_have_all_valid_fields(
    user_api_client,
    checkout_with_item,
    gift_card,
    payment_dummy_credit_card,
    address,
    shipping_method,
):
    # given
    billing_address = Address.objects.create(
        first_name="John",
        last_name="Doe",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        country="PL",
        phone="+48713988102",
        postal_code="XX-ABC",
    )  # incorrect postalCode

    checkout = checkout_with_item
    checkout.billing_address = billing_address
    checkout.shipping_method = shipping_method
    checkout.shipping_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    payment = payment_dummy_credit_card
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.token = "123"
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert len(data["errors"]) == 1

    assert data["errors"][0]["code"] == "INVALID"
    assert data["errors"][0]["field"] == "postalCode"
    assert Order.objects.count() == orders_count
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


def test_checkout_complete_with_not_normalized_shipping_address(
    site_settings,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    shipping_address = Address.objects.create(
        country="US",
        city="Washington",
        country_area="District of Columbia",
        street_address_1="1600 Pennsylvania Avenue NW",
        postal_code="20500",
    )
    checkout.shipping_address = shipping_address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = Order.objects.first()
    shipping_address = order.shipping_address
    assert shipping_address
    assert shipping_address.city == "WASHINGTON"
    assert shipping_address.country_area == "DC"


def test_checkout_complete_with_not_normalized_billing_address(
    site_settings,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    billing_address = Address.objects.create(
        country="US",
        city="Washington",
        country_area="District of Columbia",
        street_address_1="1600 Pennsylvania Avenue NW",
        postal_code="20500",
    )
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = billing_address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = Order.objects.first()
    billing_address = order.billing_address
    assert billing_address
    assert billing_address.city == "WASHINGTON"
    assert billing_address.country_area == "DC"


@patch.object(PluginsManager, "process_payment")
def test_checkout_complete_check_reservations_create(
    mocked_process_payment,
    user_api_client,
    checkout_with_item,
    address,
    payment_dummy,
    shipping_method,
    action_required_gateway_response,
):
    # given
    mocked_process_payment.return_value = action_required_gateway_response

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    orders_count = Order.objects.count()
    assert not len(Reservation.objects.all())

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]
    assert data["confirmationNeeded"] is True

    reservations = Reservation.objects.all()
    assert len(reservations) == 1
    assert reservations[0].checkout_line.checkout.token == checkout.token
    assert reservations[0].reserved_until <= timezone.now() + datetime.timedelta(
        seconds=settings.RESERVE_DURATION
    )
    assert Order.objects.count() == orders_count


def test_checkout_complete_reservations_drop(
    site_settings,
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.tax_exemption = True
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]
    assert not len(Reservation.objects.all())


@pytest.mark.django_db(transaction=True)
def test_checkout_complete_payment_create_create_run_in_meantime(
    site_settings,
    user_api_client,
    checkout_without_shipping_required,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    checkout = checkout_without_shipping_required
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    # Call CheckoutPaymentCreate mutation during the CheckoutComplete call processing.
    # CheckoutPaymentCreate should raise an error and do not influence
    # the CheckoutComplete call.
    def call_payment_create_mutation(*args, **kwargs):
        from ....payment.tests.mutations.test_checkout_payment_create import (
            CREATE_PAYMENT_MUTATION,
            DUMMY_GATEWAY,
        )

        variables = {
            "id": to_global_id_or_none(checkout),
            "input": {
                "gateway": DUMMY_GATEWAY,
                "token": "sample-token",
                "amount": total.gross.amount,
            },
        }

        response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
        data = get_graphql_content(response)["data"]["checkoutPaymentCreate"]
        assert len(data["errors"]) == 1
        assert (
            data["errors"][0]["code"]
            == PaymentErrorCode.CHECKOUT_COMPLETION_IN_PROGRESS.name
        )

    # when
    with before_after.after(
        "saleor.checkout.complete_checkout._process_payment",
        call_payment_create_mutation,
    ):
        response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    errors = data["errors"]
    assert not errors
    assert data["order"]


@pytest.mark.django_db(transaction=True)
def test_checkout_complete_payment_payment_deactivated_in_meantime(
    site_settings,
    user_api_client,
    checkout_without_shipping_required,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    checkout = checkout_without_shipping_required
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    def deactivate_payment(*args, **kwargs):
        payment.is_active = False
        payment.save(update_fields=["is_active"])

    # when
    with before_after.after(
        "saleor.checkout.complete_checkout._process_payment",
        deactivate_payment,
    ):
        response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.INACTIVE_PAYMENT.name
    checkout.refresh_from_db()
    assert not checkout.completing_started_at


@pytest.mark.integration
def test_checkout_complete_line_deleted_in_the_meantime(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    payment_dummy,
    address,
    shipping_method,
):
    # given
    assert not gift_card.last_used_on

    checkout = checkout_with_gift_card
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.tax_exemption = True
    checkout.save()
    checkout.metadata_storage.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    channel = checkout.channel
    channel.automatically_confirm_all_new_orders = True
    channel.save()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    orders_count = Order.objects.count()
    redirect_url = "https://www.example.com"
    variables = {"id": to_global_id_or_none(checkout), "redirectUrl": redirect_url}

    def delete_order_line(*args, **kwargs):
        CheckoutLine.objects.get(id=checkout.lines.first().id).delete()

    # when
    with before_after.before(
        "saleor.graphql.checkout.mutations.checkout_complete.complete_checkout",
        delete_order_line,
    ):
        response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]

    assert data["order"]
    assert not data["errors"]
    assert Order.objects.count() == orders_count + 1
    assert not Checkout.objects.filter(pk=checkout.pk).exists()


def test_checkout_complete_with_invalid_address(
    api_client, checkout_with_item, address, payment_dummy, shipping_method
):
    """Check if checkout can be completed with invalid address.

    After introducing `AddressInput.skip_validation`, Saleor may have invalid address
    stored in database.
    """
    # given
    checkout = checkout_with_item
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    invalid_postal_code = "invalid postal code"
    address.postal_code = invalid_postal_code
    address.validation_skipped = True
    address.save(update_fields=["validation_skipped", "postal_code"])

    checkout.billing_address = address
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save(
        update_fields=["billing_address", "shipping_address", "shipping_method"]
    )

    # Create a dummy payment to charge
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)["data"]["checkoutComplete"]

    # then
    assert not content["errors"]
    order = Order.objects.get(checkout_token=checkout.token)
    assert order.shipping_address.postal_code == invalid_postal_code
    assert order.billing_address.postal_code == invalid_postal_code


@patch("saleor.checkout.complete_checkout._get_unit_discount_reason")
def test_checkout_complete_log_unknown_discount_reason(
    mocked_discount_reason,
    user_api_client,
    checkout_with_item_and_voucher_specific_products,
    voucher_specific_product_type,
    payment_dummy,
    address,
    shipping_method,
    caplog,
):
    # given
    mocked_discount_reason.return_value = None

    checkout = checkout_with_item_and_voucher_specific_products
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save(
        update_fields=["shipping_address", "shipping_method", "billing_address"]
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert not data["errors"]

    order = Order.objects.first()
    order_line = order.lines.first()
    assert not order_line.unit_discount_reason
    assert "Unknown discount reason" in caplog.text
    assert caplog.records[0].checkout_id == to_global_id_or_none(checkout)
