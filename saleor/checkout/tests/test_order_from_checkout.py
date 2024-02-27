from decimal import Decimal
from unittest import mock

import before_after
import pytest
from django.test import override_settings
from prices import Money, TaxedMoney

from ...checkout.models import Checkout, CheckoutLine
from ...core.exceptions import InsufficientStock
from ...core.prices import quantize_price
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
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, [], manager)

    add_variant_to_checkout(checkout_info, variant, 10, check_quantity=False)
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.tracking_code = "tracking_code"
    checkout.save()

    checkout_lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, checkout_lines, manager)
    lines, _ = fetch_checkout_lines(checkout)
    with pytest.raises(InsufficientStock):
        create_order_from_checkout(
            checkout_info=checkout_info,
            manager=manager,
            user=None,
            app=app,
        )


@pytest.mark.parametrize("is_anonymous_user", [True, False])
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

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
        manager=manager,
        user=None,
        app=app,
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

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
    checkout_info = fetch_checkout_info(checkout, checkout_lines, manager)

    order = create_order_from_checkout(
        checkout_info=checkout_info,
        manager=manager,
        user=None,
        app=app,
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


def test_create_order_with_many_gift_cards_worth_more_than_total(
    checkout_with_items_and_shipping,
    gift_card_created_by_staff,
    gift_card,
    customer_user,
    shipping_method,
    app,
):
    # given
    gift_card_1 = gift_card_created_by_staff
    gift_card_2 = gift_card
    checkout = checkout_with_items_and_shipping
    checkout.user = customer_user
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    price_without_gift_card = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    gift_card_2_old_balance = gift_card_2.current_balance.amount
    gift_card_2_balance_halved = gift_card_2_old_balance / 2
    gift_card_2_new_balance = (
        price_without_gift_card.gross.amount - gift_card_2_balance_halved
    )

    gift_card_2.current_balance_amount = gift_card_2_new_balance
    gift_card_2.initial_balance_amount = gift_card_2_new_balance
    gift_card_2.save()
    gift_cards_balance_before_order = (
        gift_card_1.current_balance.amount + gift_card_2.current_balance.amount
    )
    checkout.gift_cards.add(gift_card_2, gift_card_1)
    checkout.save()
    checkout_lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, checkout_lines, manager)

    # when
    order = create_order_from_checkout(
        checkout_info=checkout_info,
        manager=manager,
        user=None,
        app=app,
    )
    gift_card_1.refresh_from_db()
    gift_card_2.refresh_from_db()
    zero_price = zero_money(gift_card.currency)

    # then
    assert order.gift_cards.count() == 2
    assert gift_card_1.current_balance == zero_price
    assert gift_card_2.current_balance.amount == gift_card_2_balance_halved
    assert price_without_gift_card.gross.amount == (
        gift_cards_balance_before_order - gift_card_2_balance_halved
    )
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card_created_by_staff, type=GiftCardEvents.USED_IN_ORDER
    )
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.USED_IN_ORDER
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

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
    checkout_info = fetch_checkout_info(checkout, checkout_lines, manager)

    order = create_order_from_checkout(
        checkout_info=checkout_info,
        manager=manager,
        user=None,
        app=app,
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
@pytest.mark.parametrize("is_anonymous_user", [True, False])
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

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
        manager=manager,
        user=None,
        app=app,
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
@pytest.mark.parametrize("is_anonymous_user", [True, False])
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
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    shippable_variant = shippable_gift_card_product.variants.get()
    add_variant_to_checkout(checkout_info, shippable_variant, 2)

    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

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
        manager=manager,
        user=None,
        app=app,
    )

    assert order.total.gross == total_gross
    assert not GiftCard.objects.all()
    send_notification_mock.assert_not_called()


@pytest.mark.parametrize("is_anonymous_user", [True, False])
def test_create_order_gift_card_bought_do_not_fulfill_gift_cards_automatically(
    site_settings,
    checkout_with_gift_card_items,
    customer_user,
    shipping_method,
    is_anonymous_user,
    non_shippable_gift_card_product,
    app,
):
    channel = checkout_with_gift_card_items.channel
    channel.automatically_fulfill_non_shippable_gift_card = False
    channel.save()

    checkout_user = None if is_anonymous_user else customer_user
    checkout = checkout_with_gift_card_items
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

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
        manager=manager,
        user=None,
        app=app,
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
    manager = get_plugins_manager(allow_replica=False)

    checkout_lines, unavailable_variant_pks = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, checkout_lines, manager)

    order = create_order_from_checkout(
        checkout_info=checkout_info,
        manager=manager,
        user=None,
        app=app,
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

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
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
        manager=manager,
        user=None,
        app=app,
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
    manager = get_plugins_manager(allow_replica=False)

    checkout_lines, unavailable_variant_pks = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, checkout_lines, manager)

    # when
    order = create_order_from_checkout(
        checkout_info=checkout_info,
        manager=manager,
        user=None,
        app=app,
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
    manager = get_plugins_manager(allow_replica=False)

    checkout_lines, unavailable_variant_pks = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, checkout_lines, manager)

    # when
    order = create_order_from_checkout(
        checkout_info=checkout_info,
        manager=manager,
        user=None,
        app=app,
    )

    # then
    assert order.total_charged_amount == charged_value


def test_create_order_from_checkout_update_display_gross_prices(
    checkout_with_item, app
):
    # given
    checkout = checkout_with_item
    channel = checkout.channel
    tax_configuration = channel.tax_configuration

    tax_configuration.display_gross_prices = False
    tax_configuration.save()
    tax_configuration.country_exceptions.all().delete()

    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, [], manager)
    checkout_lines, _ = fetch_checkout_lines(checkout)

    # when
    order = create_order_from_checkout(
        checkout_info=checkout_info,
        manager=manager,
        user=None,
        app=app,
    )

    # then
    assert not order.display_gross_prices


def test_create_order_from_checkout_store_shipping_prices(
    checkout_with_items_and_shipping, shipping_method, customer_user, app
):
    # given
    checkout = checkout_with_items_and_shipping

    expected_base_shipping_price = shipping_method.channel_listings.get(
        channel=checkout.channel
    ).price
    expected_shipping_price = TaxedMoney(
        net=expected_base_shipping_price * Decimal("0.9"),
        gross=expected_base_shipping_price,
    )
    expected_shipping_tax_rate = Decimal("0.1")

    manager = get_plugins_manager(allow_replica=False)
    manager.get_checkout_shipping_tax_rate = mock.Mock(
        return_value=expected_shipping_tax_rate
    )
    manager.calculate_checkout_shipping = mock.Mock(
        return_value=expected_shipping_price
    )

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    order = create_order_from_checkout(
        checkout_info=checkout_info,
        manager=manager,
        user=None,
        app=app,
    )

    # then
    assert order.base_shipping_price == expected_base_shipping_price
    assert order.shipping_price == expected_shipping_price
    manager.calculate_checkout_shipping.assert_called_once_with(
        mock.ANY, lines, checkout.shipping_address, plugin_ids=None
    )
    assert order.shipping_tax_rate == expected_shipping_tax_rate
    manager.get_checkout_shipping_tax_rate.assert_called_once_with(
        mock.ANY,
        lines,
        checkout.shipping_address,
        expected_shipping_price,
        plugin_ids=None,
    )


def test_create_order_from_checkout_valid_undiscounted_prices(
    checkout_with_items_and_shipping, shipping_method, customer_user, app
):
    # given
    checkout = checkout_with_items_and_shipping
    tc = checkout.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.tax_calculation_strategy = "FLAT_RATES"
    tc.prices_entered_with_tax = False
    tc.save()
    line = checkout.lines.first()
    product = line.variant.product
    product.tax_class.country_rates.update_or_create(
        country=checkout.shipping_address.country.code, defaults={"rate": 7.75}
    )
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)

    checkout_info = fetch_checkout_info(checkout, lines, manager, [])

    # when
    order = create_order_from_checkout(
        checkout_info=checkout_info,
        manager=manager,
        user=None,
        app=app,
    )

    # then
    for line in order.lines.all():
        expected_gross = quantize_price(
            Money((line.base_unit_price.amount * (1 + line.tax_rate)), line.currency),
            line.currency,
        )
        expected_undiscounted_unit_price = TaxedMoney(
            net=line.base_unit_price,
            gross=expected_gross,
        )

        assert line.undiscounted_unit_price == expected_undiscounted_unit_price
        expected_total_gross = quantize_price(
            Money(
                (line.base_unit_price.amount * (1 + line.tax_rate)) * line.quantity,
                line.currency,
            ),
            line.currency,
        )
        expected_undiscounted_total_price = TaxedMoney(
            net=line.base_unit_price * line.quantity,
            gross=expected_total_gross,
        )
        assert line.undiscounted_total_price == expected_undiscounted_total_price


def test_create_order_from_store_shipping_prices_with_free_shipping_voucher(
    checkout_with_voucher_free_shipping,
    shipping_method,
    customer_user,
    voucher_free_shipping,
    app,
):
    # given
    checkout = checkout_with_voucher_free_shipping

    expected_base_shipping_price = zero_money(checkout.currency)
    expected_shipping_price = zero_taxed_money(checkout.currency)
    expected_shipping_tax_rate = Decimal("0.0")

    manager = get_plugins_manager(allow_replica=False)
    manager.get_checkout_shipping_tax_rate = mock.Mock(
        return_value=expected_shipping_tax_rate
    )
    manager.calculate_checkout_shipping = mock.Mock(
        return_value=expected_shipping_price
    )

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    order = create_order_from_checkout(
        checkout_info=checkout_info,
        manager=manager,
        user=None,
        app=app,
    )

    # then
    assert order.base_shipping_price == expected_base_shipping_price
    assert order.shipping_price == expected_shipping_price
    manager.calculate_checkout_shipping.assert_called_once_with(
        mock.ANY, lines, checkout.shipping_address, plugin_ids=None
    )
    assert order.shipping_tax_rate == expected_shipping_tax_rate
    manager.get_checkout_shipping_tax_rate.assert_called_once_with(
        mock.ANY,
        lines,
        checkout.shipping_address,
        expected_shipping_price,
        plugin_ids=None,
    )


def test_note_in_created_order_checkout_line_deleted_in_the_meantime(
    checkout_with_item, address, shipping_method, app, voucher_percentage
):
    # given
    checkout_with_item.voucher_code = voucher_percentage.code
    checkout_with_item.shipping_address = address
    checkout_with_item.billing_address = address
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.tracking_code = "tracking_code"
    checkout_with_item.redirect_url = "https://www.example.com"
    checkout_with_item.save()
    manager = get_plugins_manager(allow_replica=False)

    checkout_lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, checkout_lines, manager)

    def delete_checkout_line(*args, **kwargs):
        CheckoutLine.objects.get(id=checkout_with_item.lines.first().id).delete()

    # when
    with before_after.after(
        "saleor.checkout.complete_checkout._increase_voucher_code_usage_value",
        delete_checkout_line,
    ):
        order = create_order_from_checkout(
            checkout_info=checkout_info,
            manager=manager,
            user=None,
            app=app,
        )

    # then
    assert order


def test_note_in_created_order_checkout_deleted_in_the_meantime(
    checkout_with_item, address, shipping_method, app, voucher_percentage
):
    # given
    checkout_with_item.voucher_code = voucher_percentage.code
    checkout_with_item.shipping_address = address
    checkout_with_item.billing_address = address
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.tracking_code = "tracking_code"
    checkout_with_item.redirect_url = "https://www.example.com"
    checkout_with_item.save()
    manager = get_plugins_manager(allow_replica=False)

    checkout_lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, checkout_lines, manager)

    def delete_checkout(*args, **kwargs):
        Checkout.objects.get(pk=checkout_with_item.pk).delete()

    # when
    with before_after.after(
        "saleor.checkout.complete_checkout._increase_voucher_code_usage_value",
        delete_checkout,
    ):
        order = create_order_from_checkout(
            checkout_info=checkout_info,
            manager=manager,
            user=None,
            app=app,
        )

    # then
    assert order is None


@mock.patch("saleor.checkout.calculations.checkout_line_total")
@mock.patch("saleor.checkout.calculations.checkout_line_unit_price")
def test_create_order_from_checkout_update_undiscounted_prices_match(
    mock_unit,
    mock_total,
    checkout_with_items_and_shipping,
    shipping_method,
    customer_user,
    app,
):
    # given
    checkout = checkout_with_items_and_shipping
    tc = checkout.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.tax_calculation_strategy = "TAX_APP"
    tc.prices_entered_with_tax = False
    tc.save()

    # mock tax app returning different prices than local calculations
    expected_price = TaxedMoney(
        net=Money("35.000", "USD"),
        gross=Money("37.720", "USD"),
    )
    mock_unit.return_value = expected_price
    mock_total.return_value = expected_price

    manager = get_plugins_manager(allow_replica=False)
    country_code = checkout.shipping_address.country.code
    line = checkout.lines.first()
    line.quantity = 1
    line.save()
    product = line.variant.product
    channel_listing = line.variant.channel_listings.first()

    channel_listing.price = Money("35.000", "USD")
    channel_listing.save()
    product.tax_class.country_rates.update_or_create(
        country=country_code, defaults={"rate": 7.75}
    )
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager, [])

    # when
    order = create_order_from_checkout(
        checkout_info=checkout_info,
        manager=manager,
        user=None,
        app=app,
    )
    line = order.lines.first()
    assert line.unit_price == line.undiscounted_unit_price
    assert line.total_price == line.undiscounted_total_price


def test_create_order_product_on_promotion(
    checkout_with_item_on_promotion,
    customer_user,
    shipping_method,
    app,
    catalogue_promotion_without_rules,
):
    # given
    checkout = checkout_with_item_on_promotion
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.tracking_code = "tracking_code"
    checkout.redirect_url = "https://www.example.com"
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    order = create_order_from_checkout(
        checkout_info=checkout_info,
        manager=manager,
        user=None,
        app=app,
    )

    # then
    assert order.lines.count() == 1
    line = order.lines.first()
    assert line.discounts.count() == 1
    assert line.sale_id
    assert line.unit_discount_amount
    assert line.unit_discount_reason
    assert line.discounts.count() == 1
    discount = line.discounts.first()
    assert discount.promotion_rule
    assert (
        discount.amount_value == (order.undiscounted_total - order.total).gross.amount
    )
