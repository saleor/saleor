import datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from ....plugins.manager import get_plugins_manager
from ....product.models import ProductVariantChannelListing
from ...fetch import fetch_checkout_info, fetch_checkout_lines
from ...models import Checkout, CheckoutLine, CheckoutMetadata
from ...utils import add_variant_to_checkout


@pytest.fixture
def checkout(db, channel_USD, settings):
    checkout = Checkout.objects.create(
        currency=channel_USD.currency_code,
        channel=channel_USD,
        price_expiration=timezone.now() + settings.CHECKOUT_PRICES_TTL,
        email="user@email.com",
    )
    checkout.set_country("US", commit=True)
    CheckoutMetadata.objects.create(checkout=checkout)
    return checkout


@pytest.fixture
def checkout_JPY(channel_JPY):
    checkout = Checkout.objects.create(
        currency=channel_JPY.currency_code, channel=channel_JPY
    )
    checkout.set_country("JP", commit=True)
    return checkout


@pytest.fixture
def checkout_with_item(checkout, product):
    variant = product.variants.first()
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 3)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_item_and_tax_exemption(checkout_with_item):
    checkout_with_item.tax_exemption = True
    checkout_with_item.save(update_fields=["tax_exemption"])
    return checkout_with_item


@pytest.fixture
def checkout_with_same_items_in_multiple_lines(checkout, product):
    variant = product.variants.first()
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 1)
    add_variant_to_checkout(checkout_info, variant, 1, force_new_line=True)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_item_total_0(checkout, product_price_0):
    variant = product_price_0.variants.get()
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 1)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_JPY_with_item(checkout_JPY, product_in_channel_JPY):
    variant = product_in_channel_JPY.variants.get()
    checkout_info = fetch_checkout_info(
        checkout_JPY, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 3)
    checkout_JPY.save()
    return checkout_JPY


@pytest.fixture
def checkouts_list(channel_USD, channel_PLN):
    checkouts_usd = Checkout.objects.bulk_create(
        [
            Checkout(currency=channel_USD.currency_code, channel=channel_USD),
            Checkout(currency=channel_USD.currency_code, channel=channel_USD),
            Checkout(currency=channel_USD.currency_code, channel=channel_USD),
        ]
    )
    checkouts_pln = Checkout.objects.bulk_create(
        [
            Checkout(currency=channel_PLN.currency_code, channel=channel_PLN),
            Checkout(currency=channel_PLN.currency_code, channel=channel_PLN),
        ]
    )
    return [*checkouts_pln, *checkouts_usd]


@pytest.fixture
def checkouts_assigned_to_customer(channel_USD, channel_PLN, customer_user):
    return Checkout.objects.bulk_create(
        [
            Checkout(
                currency=channel_USD.currency_code,
                channel=channel_USD,
                user=customer_user,
            ),
            Checkout(
                currency=channel_PLN.currency_code,
                channel=channel_PLN,
                user=customer_user,
            ),
        ]
    )


@pytest.fixture
def checkout_ready_to_complete(checkout_with_item, address, shipping_method, gift_card):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout_with_item.gift_cards.add(gift_card)
    checkout.save()
    checkout.metadata_storage.save()
    return checkout


@pytest.fixture
def checkout_with_digital_item(checkout, digital_content, address):
    """Create a checkout with a digital line."""
    variant = digital_content.product_variant
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 1)
    checkout.discount_amount = Decimal(0)
    checkout.billing_address = address
    checkout.email = "customer@example.com"
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_shipping_required(checkout_with_item, product):
    checkout = checkout_with_item
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 3)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_item_and_shipping_method(checkout_with_item, shipping_method):
    checkout = checkout_with_item
    checkout.shipping_method = shipping_method
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_shipping_method(checkout_with_shipping_address, shipping_method):
    checkout = checkout_with_shipping_address

    checkout.shipping_method = shipping_method
    checkout.save()

    return checkout


@pytest.fixture
def checkout_without_shipping_required(checkout, product_without_shipping):
    variant = product_without_shipping.variants.get()
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 1)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_single_item(checkout, product):
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 1)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_variant_without_inventory_tracking(
    checkout, variant_without_inventory_tracking, address, shipping_method
):
    variant = variant_without_inventory_tracking
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 1)
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()
    return checkout


@pytest.fixture
def checkout_with_variants(
    checkout,
    stock,
    product_with_default_variant,
    product_with_single_variant,
    product_with_two_variants,
):
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )

    add_variant_to_checkout(
        checkout_info, product_with_default_variant.variants.get(), 1
    )
    add_variant_to_checkout(
        checkout_info, product_with_single_variant.variants.get(), 10
    )
    add_variant_to_checkout(
        checkout_info, product_with_two_variants.variants.first(), 3
    )
    add_variant_to_checkout(checkout_info, product_with_two_variants.variants.last(), 5)

    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_shipping_address(checkout_with_variants, address):
    checkout = checkout_with_variants

    checkout.shipping_address = address.get_copy()
    checkout.save()

    return checkout


@pytest.fixture
def checkout_with_billing_address(checkout_with_shipping_method, address):
    checkout = checkout_with_shipping_method

    checkout.billing_address = address
    checkout.save()

    return checkout


@pytest.fixture
def checkout_with_variants_for_cc(
    checkout, stocks_for_cc, product_variant_list, product_with_two_variants
):
    channel_listings_map = {
        listing.variant_id: listing
        for listing in ProductVariantChannelListing.objects.filter(
            channel_id=checkout.channel_id,
            variant__in=product_variant_list
            + [product_with_two_variants.variants.last()],
        )
    }

    CheckoutLine.objects.bulk_create(
        [
            CheckoutLine(
                checkout=checkout,
                variant=product_variant_list[0],
                quantity=3,
                currency="USD",
                undiscounted_unit_price_amount=channel_listings_map.get(
                    product_variant_list[0].id
                ).price_amount,
            ),
            CheckoutLine(
                checkout=checkout,
                variant=product_variant_list[1],
                quantity=10,
                currency="USD",
                undiscounted_unit_price_amount=channel_listings_map.get(
                    product_variant_list[0].id
                ).price_amount,
            ),
            CheckoutLine(
                checkout=checkout,
                variant=product_with_two_variants.variants.last(),
                quantity=5,
                currency="USD",
                undiscounted_unit_price_amount=channel_listings_map.get(
                    product_variant_list[0].id
                ).price_amount,
            ),
        ]
    )
    return checkout


@pytest.fixture
def checkout_with_shipping_address_for_cc(checkout_with_variants_for_cc, address):
    checkout = checkout_with_variants_for_cc

    checkout.shipping_address = address.get_copy()
    checkout.save()

    return checkout


@pytest.fixture
def checkout_with_billing_address_for_cc(checkout_with_delivery_method_for_cc, address):
    checkout = checkout_with_delivery_method_for_cc

    checkout.billing_address = address
    checkout.save()

    return checkout


@pytest.fixture
def checkout_with_delivery_method_for_cc(
    warehouses_for_cc, checkout_with_shipping_address_for_cc
):
    checkout = checkout_with_shipping_address_for_cc
    checkout.collection_point = warehouses_for_cc[1]

    checkout.save()

    return checkout


@pytest.fixture
def checkout_with_items(checkout, product_list, product):
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 1)
    for prod in product_list:
        variant = prod.variants.get()
        add_variant_to_checkout(checkout_info, variant, 1)
    checkout.save()
    checkout.refresh_from_db()
    return checkout


@pytest.fixture
def checkout_with_items_and_shipping(checkout_with_items, address, shipping_method):
    checkout_with_items.shipping_address = address
    checkout_with_items.shipping_method = shipping_method
    checkout_with_items.billing_address = address
    checkout_with_items.save()
    return checkout_with_items


@pytest.fixture
def checkout_with_item_and_shipping(checkout_with_item, address, shipping_method):
    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.billing_address = address
    checkout_with_item.save()
    return checkout_with_item


@pytest.fixture
def checkout_with_gift_card(checkout_with_item, gift_card):
    checkout_with_item.gift_cards.add(gift_card)
    checkout_with_item.save()
    return checkout_with_item


@pytest.fixture
def checkout_with_preorders_only(
    checkout,
    stocks_for_cc,
    preorder_variant_with_end_date,
    preorder_variant_channel_threshold,
):
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines, get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, preorder_variant_with_end_date, 2)
    add_variant_to_checkout(checkout_info, preorder_variant_channel_threshold, 2)

    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_preorders_and_regular_variant(
    checkout, stocks_for_cc, preorder_variant_with_end_date, product_variant_list
):
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines, get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, preorder_variant_with_end_date, 2)
    add_variant_to_checkout(checkout_info, product_variant_list[0], 2)

    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_gift_card_items(
    checkout, non_shippable_gift_card_product, shippable_gift_card_product
):
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    non_shippable_variant = non_shippable_gift_card_product.variants.get()
    shippable_variant = shippable_gift_card_product.variants.get()
    add_variant_to_checkout(checkout_info, non_shippable_variant, 1)
    add_variant_to_checkout(checkout_info, shippable_variant, 2)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_item_and_preorder_item(
    checkout_with_item, product, preorder_variant_channel_threshold
):
    checkout_info = fetch_checkout_info(
        checkout_with_item, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, preorder_variant_channel_threshold, 1)
    return checkout_with_item


@pytest.fixture
def checkout_with_problems(
    checkout_with_items,
    product_type,
    address,
    shipping_method,
    category,
    default_tax_class,
    channel_USD,
    warehouse,
):
    checkout_with_items.shipping_address = address
    checkout_with_items.billing_address = address
    checkout_with_items.shipping_method = shipping_method
    checkout_with_items.save(
        update_fields=["shipping_address", "shipping_method", "billing_address"]
    )

    first_line = checkout_with_items.lines.first()
    first_line.variant.track_inventory = True
    first_line.variant.save(update_fields=["track_inventory"])

    product_type = first_line.variant.product.product_type
    product_type.is_shipping_required = True
    product_type.save(update_fields=["is_shipping_required"])

    first_line.variant.stocks.all().delete()

    second_line = checkout_with_items.lines.last()

    available_at = datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=5)
    product = second_line.variant.product
    product.channel_listings.update(
        available_for_purchase_at=available_at, is_published=False
    )

    return checkout_with_items


@pytest.fixture
def user_checkout(customer_user, channel_USD):
    checkout = Checkout.objects.create(
        user=customer_user,
        channel=channel_USD,
        billing_address=customer_user.default_billing_address,
        shipping_address=customer_user.default_shipping_address,
        note="Test notes",
        currency="USD",
    )
    CheckoutMetadata.objects.create(checkout=checkout)
    return checkout


@pytest.fixture
def user_checkout_for_cc(customer_user, channel_USD, warehouse_for_cc):
    checkout = Checkout.objects.create(
        user=customer_user,
        email=customer_user.email,
        channel=channel_USD,
        billing_address=customer_user.default_billing_address,
        shipping_address=warehouse_for_cc.address,
        collection_point=warehouse_for_cc,
        note="Test notes",
        currency="USD",
    )
    return checkout


@pytest.fixture
def user_checkout_PLN(customer_user, channel_PLN):
    checkout = Checkout.objects.create(
        user=customer_user,
        channel=channel_PLN,
        billing_address=customer_user.default_billing_address,
        shipping_address=customer_user.default_shipping_address,
        note="Test notes",
        currency="PLN",
    )
    return checkout


@pytest.fixture
def user_checkout_with_items(user_checkout, product_list):
    checkout_info = fetch_checkout_info(
        user_checkout, [], get_plugins_manager(allow_replica=False)
    )
    for product in product_list:
        variant = product.variants.get()
        add_variant_to_checkout(checkout_info, variant, 1)
    user_checkout.refresh_from_db()
    return user_checkout


@pytest.fixture
def user_checkout_with_items_for_cc(user_checkout_for_cc, product_list):
    checkout_info = fetch_checkout_info(
        user_checkout_for_cc, [], get_plugins_manager(allow_replica=False)
    )
    for product in product_list:
        variant = product.variants.get()
        add_variant_to_checkout(checkout_info, variant, 1)
    user_checkout_for_cc.refresh_from_db()
    return user_checkout_for_cc


@pytest.fixture
def user_checkouts(request, user_checkout_with_items, user_checkout_with_items_for_cc):
    if request.param == "regular":
        return user_checkout_with_items
    if request.param == "click_and_collect":
        return user_checkout_with_items_for_cc
    raise ValueError("Internal test error")


@pytest.fixture
def customer_checkout(customer_user, checkout_with_voucher_percentage_and_shipping):
    checkout_with_voucher_percentage_and_shipping.user = customer_user
    checkout_with_voucher_percentage_and_shipping.save()
    return checkout_with_voucher_percentage_and_shipping


@pytest.fixture
def checkout_for_cc(channel_USD, customer_user):
    checkout = Checkout.objects.create(
        channel=channel_USD,
        billing_address=customer_user.default_billing_address,
        shipping_address=customer_user.default_shipping_address,
        note="Test notes",
        currency="USD",
        email=customer_user.email,
    )
    CheckoutMetadata.objects.create(checkout=checkout)
    return checkout


@pytest.fixture
def checkout_with_item_for_cc(checkout_for_cc, product_variant_list):
    listing = product_variant_list[0].channel_listings.get(
        channel_id=checkout_for_cc.channel_id
    )
    CheckoutLine.objects.create(
        checkout=checkout_for_cc,
        variant=product_variant_list[0],
        quantity=1,
        currency=checkout_for_cc.currency,
        undiscounted_unit_price_amount=listing.price_amount,
    )
    return checkout_for_cc


@pytest.fixture
def checkout_with_items_for_cc(checkout_for_cc, product_variant_list):
    (
        ProductVariantChannelListing.objects.create(
            variant=product_variant_list[2],
            channel=checkout_for_cc.channel,
            cost_price_amount=Decimal(1),
            price_amount=Decimal(10),
            discounted_price_amount=Decimal(10),
            currency=checkout_for_cc.channel.currency_code,
        ),
    )
    channel_listings_map = {
        listing.variant_id: listing
        for listing in ProductVariantChannelListing.objects.filter(
            channel_id=checkout_for_cc.channel_id, variant__in=product_variant_list
        )
    }

    CheckoutLine.objects.bulk_create(
        [
            CheckoutLine(
                checkout=checkout_for_cc,
                variant=product_variant_list[0],
                quantity=1,
                currency=checkout_for_cc.currency,
                undiscounted_unit_price_amount=channel_listings_map.get(
                    product_variant_list[0].id
                ).price_amount,
            ),
            CheckoutLine(
                checkout=checkout_for_cc,
                variant=product_variant_list[1],
                quantity=1,
                currency=checkout_for_cc.currency,
                undiscounted_unit_price_amount=channel_listings_map.get(
                    product_variant_list[1].id
                ).price_amount,
            ),
            CheckoutLine(
                checkout=checkout_for_cc,
                variant=product_variant_list[2],
                quantity=1,
                currency=checkout_for_cc.currency,
                undiscounted_unit_price_amount=channel_listings_map.get(
                    product_variant_list[2].id
                ).price_amount,
            ),
        ]
    )
    checkout_for_cc.set_country("US", commit=True)

    return checkout_for_cc


@pytest.fixture
def checkout_with_line_without_listing(checkout_with_items):
    line = checkout_with_items.lines.first()
    line.quantity = 2
    line.save()
    line.variant.channel_listings.filter(
        channel_id=checkout_with_items.channel_id
    ).delete()
    return checkout_with_items, line
