from decimal import Decimal
from unittest import mock

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings

from ...core.exceptions import InsufficientStock
from ...core.taxes import zero_money, zero_taxed_money
from ...giftcard import GiftCardEvents
from ...giftcard.models import GiftCard, GiftCardEvent
from ...plugins.manager import get_plugins_manager
from ...product.models import ProductTranslation, ProductVariantTranslation
from ...tests.utils import flush_post_commit_hooks
from .. import calculations
from ..complete_checkout import create_order_from_checkout
from ..fetch import fetch_checkout_info, fetch_checkout_lines
from ..utils import add_variant_to_checkout


def test_create_order_insufficient_stock(
    checkout, customer_user, product_without_shipping, app
):
    variant = product_without_shipping.variants.get()
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, [], [], manager)

    add_variant_to_checkout(checkout_info, variant, 10, check_quantity=False)
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.tracking_code = "tracking_code"
    checkout.save()

    checkout_lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, checkout_lines, [], manager)
    lines, _ = fetch_checkout_lines(checkout)
    with pytest.raises(InsufficientStock):
        create_order_from_checkout(
            checkout_info=checkout_info,
            checkout_lines=checkout_lines,
            discounts=[],
            manager=manager,
            user=AnonymousUser(),
            app=app,
            tracking_code="tracking_code",
        )


@pytest.mark.parametrize("is_anonymous_user", (True, False))
def test_create_order_with_gift_card(
    checkout_with_gift_card, customer_user, shipping_method, is_anonymous_user, app
):
    checkout_user = None if is_anonymous_user else customer_user
    checkout = checkout_with_gift_card
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    shipping_price = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    total_gross_without_gift_cards = (
        subtotal.gross + shipping_price.gross - checkout.discount
    )
    gift_cards_balance = checkout.get_total_gift_cards_balance()

    order = create_order_from_checkout(
        checkout_info=checkout_info,
        checkout_lines=lines,
        discounts=[],
        manager=manager,
        user=AnonymousUser(),
        app=app,
        tracking_code="tracking_code",
    )

    assert order.gift_cards.count() == 1
    gift_card = order.gift_cards.first()
    assert gift_card.current_balance.amount == 0
    assert order.total.gross == (total_gross_without_gift_cards - gift_cards_balance)
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )


def test_create_order_with_gift_card_partial_use(
    checkout_with_item, gift_card_used, customer_user, shipping_method, app
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    price_without_gift_card = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    gift_card_balance_before_order = gift_card_used.current_balance_amount

    checkout.gift_cards.add(gift_card_used)
    checkout.save()

    checkout_lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, checkout_lines, [], manager)

    order = create_order_from_checkout(
        checkout_info=checkout_info,
        checkout_lines=checkout_lines,
        discounts=[],
        manager=manager,
        user=AnonymousUser(),
        app=app,
        tracking_code="tracking_code",
    )

    gift_card_used.refresh_from_db()

    expected_old_balance = (
        price_without_gift_card.gross.amount + gift_card_used.current_balance_amount
    )

    assert order.gift_cards.count() > 0
    assert order.total == zero_taxed_money(order.currency)
    assert gift_card_balance_before_order == expected_old_balance
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card_used, type=GiftCardEvents.USED_IN_ORDER
    )


def test_create_order_with_many_gift_cards(
    checkout_with_item,
    gift_card_created_by_staff,
    gift_card,
    customer_user,
    shipping_method,
    app,
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    price_without_gift_card = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    gift_cards_balance_before_order = (
        gift_card_created_by_staff.current_balance.amount
        + gift_card.current_balance.amount
    )

    checkout.gift_cards.add(gift_card_created_by_staff)
    checkout.gift_cards.add(gift_card)
    checkout.save()

    checkout_lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, checkout_lines, [], manager)

    order = create_order_from_checkout(
        checkout_info=checkout_info,
        checkout_lines=checkout_lines,
        discounts=[],
        manager=manager,
        user=AnonymousUser,
        app=app,
        tracking_code="tracking_code",
    )

    gift_card_created_by_staff.refresh_from_db()
    gift_card.refresh_from_db()
    zero_price = zero_money(gift_card.currency)
    assert order.gift_cards.count() > 0
    assert gift_card_created_by_staff.current_balance == zero_price
    assert gift_card.current_balance == zero_price
    assert price_without_gift_card.gross.amount == (
        gift_cards_balance_before_order + order.total.gross.amount
    )
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card_created_by_staff, type=GiftCardEvents.USED_IN_ORDER
    )
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
    )


@mock.patch("saleor.giftcard.utils.send_gift_card_notification")
@pytest.mark.parametrize("is_anonymous_user", (True, False))
def test_create_order_gift_card_bought(
    send_notification_mock,
    checkout_with_gift_card_items,
    customer_user,
    shipping_method,
    is_anonymous_user,
    non_shippable_gift_card_product,
    app,
    payment_txn_captured,
):
    # given
    checkout_user = None if is_anonymous_user else customer_user
    checkout = checkout_with_gift_card_items
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    shipping_price = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    total_gross = subtotal.gross + shipping_price.gross - checkout.discount

    payment = payment_txn_captured
    payment.checkout = checkout
    payment.captured_amount = total_gross.amount
    payment.total = total_gross.amount
    payment.save(update_fields=["checkout", "captured_amount", "total"])

    # when
    order = create_order_from_checkout(
        checkout_info=checkout_info,
        checkout_lines=lines,
        discounts=[],
        manager=manager,
        user=AnonymousUser(),
        app=app,
        tracking_code="tracking_code",
    )

    # then
    flush_post_commit_hooks()
    assert order.total.gross == total_gross
    flush_post_commit_hooks()
    gift_card = GiftCard.objects.get()
    assert (
        gift_card.initial_balance
        == order.lines.get(
            variant=non_shippable_gift_card_product.variants.first()
        ).unit_price_gross
    )
    assert GiftCardEvent.objects.filter(gift_card=gift_card, type=GiftCardEvents.BOUGHT)
    flush_post_commit_hooks()
    send_notification_mock.assert_called_once_with(
        None,
        app,
        checkout_user,
        order.user_email,
        gift_card,
        manager,
        order.channel.slug,
        resending=False,
    )


@mock.patch("saleor.giftcard.utils.send_gift_card_notification")
@pytest.mark.parametrize("is_anonymous_user", (True, False))
def test_create_order_gift_card_bought_only_shippable_gift_card(
    send_notification_mock,
    checkout,
    shippable_gift_card_product,
    customer_user,
    shipping_method,
    is_anonymous_user,
    app,
):
    checkout_user = None if is_anonymous_user else customer_user
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    shippable_variant = shippable_gift_card_product.variants.get()
    add_variant_to_checkout(checkout_info, shippable_variant, 2)

    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    shipping_price = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    total_gross = subtotal.gross + shipping_price.gross - checkout.discount

    order = create_order_from_checkout(
        checkout_info=checkout_info,
        checkout_lines=lines,
        discounts=[],
        manager=manager,
        user=AnonymousUser(),
        app=app,
        tracking_code="tracking_code",
    )

    assert order.total.gross == total_gross
    assert not GiftCard.objects.all()
    send_notification_mock.assert_not_called()


@pytest.mark.parametrize("is_anonymous_user", (True, False))
def test_create_order_gift_card_bought_do_not_fulfill_gift_cards_automatically(
    site_settings,
    checkout_with_gift_card_items,
    customer_user,
    shipping_method,
    is_anonymous_user,
    non_shippable_gift_card_product,
    app,
):
    site_settings.automatically_fulfill_non_shippable_gift_card = False
    site_settings.save(update_fields=["automatically_fulfill_non_shippable_gift_card"])

    checkout_user = None if is_anonymous_user else customer_user
    checkout = checkout_with_gift_card_items
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    shipping_price = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    total_gross = subtotal.gross + shipping_price.gross - checkout.discount

    order = create_order_from_checkout(
        checkout_info=checkout_info,
        checkout_lines=lines,
        discounts=[],
        manager=manager,
        user=AnonymousUser(),
        app=app,
        tracking_code="tracking_code",
    )

    assert order.total.gross == total_gross
    assert not GiftCard.objects.all()


def test_note_in_created_order(
    checkout_with_item, address, customer_user, shipping_method, app
):
    checkout_with_item.shipping_address = address
    checkout_with_item.billing_address = address
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.note = "test_note"
    checkout_with_item.tracking_code = "tracking_code"
    checkout_with_item.redirect_url = "https://www.example.com"
    checkout_with_item.save()
    manager = get_plugins_manager()

    checkout_lines, unavailable_variant_pks = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, checkout_lines, [], manager)

    order = create_order_from_checkout(
        checkout_info=checkout_info,
        checkout_lines=checkout_lines,
        discounts=[],
        manager=manager,
        user=AnonymousUser(),
        app=app,
        tracking_code="tracking_code",
    )
    assert order.customer_note == checkout_with_item.note


@override_settings(LANGUAGE_CODE="fr")
def test_create_order_use_translations(
    checkout_with_item, customer_user, shipping_method, app
):
    translated_product_name = "French name"
    translated_variant_name = "French variant name"

    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = ""
    checkout.redirect_url = "https://www.example.com"
    checkout.language_code = "fr"
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    variant = lines[0].variant
    product = lines[0].product

    ProductTranslation.objects.create(
        language_code="fr",
        product=product,
        name=translated_product_name,
    )
    ProductVariantTranslation.objects.create(
        language_code="fr",
        product_variant=variant,
        name=translated_variant_name,
    )

    order = create_order_from_checkout(
        checkout_info=checkout_info,
        checkout_lines=lines,
        discounts=[],
        manager=manager,
        user=AnonymousUser(),
        app=app,
        tracking_code="tracking_code",
    )
    order_line = order.lines.first()

    assert order_line.translated_product_name == translated_product_name
    assert order_line.translated_variant_name == translated_variant_name


def test_create_order_from_checkout_updates_total_authorized_amount(
    checkout_with_item, address, customer_user, shipping_method, app
):
    # given
    checkout_with_item.shipping_address = address
    checkout_with_item.billing_address = address
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.redirect_url = "https://www.example.com"
    checkout_with_item.save()

    authorized_value = Decimal(10)
    checkout_with_item.payment_transactions.create(
        authorized_value=authorized_value,
        currency=checkout_with_item.currency,
    )
    manager = get_plugins_manager()

    checkout_lines, unavailable_variant_pks = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, checkout_lines, [], manager)

    # when
    order = create_order_from_checkout(
        checkout_info=checkout_info,
        checkout_lines=checkout_lines,
        discounts=[],
        manager=manager,
        user=AnonymousUser(),
        app=app,
        tracking_code="tracking_code",
    )

    # then
    assert order.total_authorized_amount == authorized_value


def test_create_order_from_checkout_updates_total_charged_amount(
    checkout_with_item, address, customer_user, shipping_method, app
):
    # given
    checkout_with_item.shipping_address = address
    checkout_with_item.billing_address = address
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.redirect_url = "https://www.example.com"
    checkout_with_item.save()

    charged_value = Decimal(10)
    checkout_with_item.payment_transactions.create(
        charged_value=charged_value,
        currency=checkout_with_item.currency,
    )
    checkout_with_item.payment_transactions.create(
        authorized_value=Decimal(2),
        currency=checkout_with_item.currency,
    )
    manager = get_plugins_manager()

    checkout_lines, unavailable_variant_pks = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, checkout_lines, [], manager)

    # when
    order = create_order_from_checkout(
        checkout_info=checkout_info,
        checkout_lines=checkout_lines,
        discounts=[],
        manager=manager,
        user=AnonymousUser(),
        app=app,
        tracking_code="tracking_code",
    )

    # then
    assert order.total_charged_amount == charged_value
