"""Behaviour of a variant channel listing with `is_available_for_purchase=False`.

Such a listing must behave exactly like a variant with no listing in that channel:
invisible to customers and impossible to buy, while its prices stay intact.
"""

from decimal import Decimal

import graphene
import pytest

from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.models import Checkout
from ....discount.utils.checkout import (
    create_or_update_discount_objects_from_promotion_for_checkout,
)
from ....order.error_codes import OrderErrorCode
from ....order.models import Order
from ....product.models import Product, ProductVariantChannelListing
from ....product.utils.variant_prices import update_discounted_prices_for_promotion
from ...tests.utils import get_graphql_content

PRODUCT_VARIANTS_QUERY = """
query ProductVariants($slug: String!, $channel: String) {
    product(slug: $slug, channel: $channel) {
        variants {
            id
        }
    }
}
"""

PRODUCTS_QUERY = """
query Products($channel: String!) {
    products(first: 10, channel: $channel) {
        edges {
            node {
                id
                pricing {
                    priceRange {
                        start {
                            gross {
                                amount
                            }
                        }
                    }
                }
            }
        }
    }
}
"""

MUTATION_CHECKOUT_LINES_ADD = """
mutation checkoutLinesAdd($id: ID, $lines: [CheckoutLineInput!]!) {
    checkoutLinesAdd(id: $id, lines: $lines) {
        checkout {
            id
        }
        errors {
            field
            code
            message
            variants
        }
    }
}
"""

DRAFT_ORDER_CREATE_MUTATION = """
mutation DraftCreate($input: DraftOrderCreateInput!) {
    draftOrderCreate(input: $input) {
        errors {
            field
            code
            message
            variants
        }
        order {
            id
        }
    }
}
"""


@pytest.fixture
def unavailable_variant(product, channel_USD):
    variant = product.variants.get()
    listing = variant.channel_listings.get(channel=channel_USD)
    listing.is_available_for_purchase = False
    listing.save(update_fields=("is_available_for_purchase",))
    return variant


def test_customer_cannot_see_the_variant(
    api_client, product_with_two_variants, channel_USD
):
    # given
    hidden_variant, visible_variant = product_with_two_variants.variants.order_by("pk")
    listing = hidden_variant.channel_listings.get(channel=channel_USD)
    listing.is_available_for_purchase = False
    listing.save(update_fields=("is_available_for_purchase",))
    variables = {
        "slug": product_with_two_variants.slug,
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["product"]["variants"] == [
        {"id": graphene.Node.to_global_id("ProductVariant", visible_variant.pk)}
    ]


def test_staff_still_sees_the_variant_with_its_price(
    staff_api_client, unavailable_variant, permission_manage_products, channel_USD
):
    """The whole point of the flag: staff must not lose the price."""
    # given
    query = """
        query VariantListings($id: ID!) {
            productVariant(id: $id) {
                channelListings {
                    isAvailableForPurchase
                    price {
                        amount
                    }
                }
            }
        }
    """
    listing = unavailable_variant.channel_listings.get(channel=channel_USD)
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", unavailable_variant.pk)
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    listings = content["data"]["productVariant"]["channelListings"]
    assert len(listings) == 1
    assert listings[0]["isAvailableForPurchase"] is False
    assert listings[0]["price"]["amount"] == float(listing.price_amount)


def test_product_without_any_available_variant_is_hidden(
    api_client, unavailable_variant, channel_USD
):
    # given
    variables = {"channel": channel_USD.slug}

    # when
    response = api_client.post_graphql(PRODUCTS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["products"]["edges"] == []


def test_variant_stays_visible_in_a_channel_where_it_is_available(
    api_client, product_available_in_many_channels, channel_USD, channel_PLN
):
    # given
    variant = product_available_in_many_channels.variants.get()
    listing = variant.channel_listings.get(channel=channel_USD)
    listing.is_available_for_purchase = False
    listing.save(update_fields=("is_available_for_purchase",))
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    slug = product_available_in_many_channels.slug

    # when
    usd_response = api_client.post_graphql(
        PRODUCT_VARIANTS_QUERY, {"slug": slug, "channel": channel_USD.slug}
    )
    pln_response = api_client.post_graphql(
        PRODUCT_VARIANTS_QUERY, {"slug": slug, "channel": channel_PLN.slug}
    )

    # then
    assert get_graphql_content(usd_response)["data"]["product"] is None
    assert get_graphql_content(pln_response)["data"]["product"]["variants"] == [
        {"id": variant_id}
    ]


def test_checkout_lines_add_rejects_the_variant(
    api_client, checkout, unavailable_variant
):
    # given
    assert checkout.lines.exists() is False
    variant_id = graphene.Node.to_global_id("ProductVariant", unavailable_variant.pk)
    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "lines": [{"variantId": variant_id, "quantity": 1}],
    }

    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["checkoutLinesAdd"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["variants"] == [variant_id]
    assert checkout.lines.exists() is False


def test_draft_order_create_rejects_the_variant(
    staff_api_client,
    unavailable_variant,
    permission_group_manage_orders,
    channel_USD,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variant_id = graphene.Node.to_global_id("ProductVariant", unavailable_variant.pk)
    variables = {
        "input": {
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
            "lines": [{"variantId": variant_id, "quantity": 1}],
        }
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["draftOrderCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert errors[0]["variants"] == [variant_id]
    assert Order.objects.exists() is False


def test_existing_checkout_line_reports_a_problem(
    api_client, checkout_with_item, channel_USD
):
    # given
    query = """
        query CheckoutProblems($id: ID) {
            checkout(id: $id) {
                problems {
                    __typename
                }
            }
        }
    """
    line = checkout_with_item.lines.get()
    listing = line.variant.channel_listings.get(channel=channel_USD)
    listing.is_available_for_purchase = False
    listing.save(update_fields=("is_available_for_purchase",))
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout_with_item.pk)}

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    problems = content["data"]["checkout"]["problems"]
    assert {problem["__typename"] for problem in problems} == {
        "CheckoutLineProblemVariantNotAvailable"
    }
    assert Checkout.objects.get(pk=checkout_with_item.pk).lines.exists() is True


def test_unavailable_variant_is_excluded_from_the_product_price_range(
    api_client, product_with_two_variants, channel_USD
):
    # given
    cheap_price = Decimal("10.00")
    expensive_price = Decimal("20.00")
    product = product_with_two_variants
    cheap_variant, expensive_variant = product.variants.order_by("pk")

    for variant, price in (
        (cheap_variant, cheap_price),
        (expensive_variant, expensive_price),
    ):
        variant.channel_listings.filter(channel=channel_USD).update(
            price_amount=price, discounted_price_amount=price
        )
    cheap_variant.channel_listings.filter(channel=channel_USD).update(
        is_available_for_purchase=False
    )

    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))

    # when
    response = api_client.post_graphql(PRODUCTS_QUERY, {"channel": channel_USD.slug})

    # then
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    assert len(edges) == 1
    price_range = edges[0]["node"]["pricing"]["priceRange"]
    assert price_range["start"]["gross"]["amount"] == float(expensive_price)

    product.refresh_from_db(fields=("id",))
    product_listing = product.channel_listings.get(channel=channel_USD)
    assert product_listing.discounted_price_amount == expensive_price


def test_new_listing_defaults_to_available(product_with_two_variants, channel_PLN):
    """A listing created without the flag — as `addVariants` does — is available."""
    # given
    variant = product_with_two_variants.variants.order_by("pk").first()
    assert variant.channel_listings.filter(channel=channel_PLN).exists() is False

    # when
    listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_PLN,
        price_amount=None,
        currency=channel_PLN.currency_code,
    )

    # then
    assert listing.is_available_for_purchase is True
    assert listing.is_sellable is False


def test_price_less_listing_stays_unsellable_despite_the_default(
    api_client, product_with_two_variants, channel_USD
):
    # given
    variant = product_with_two_variants.variants.order_by("pk").first()
    variant.channel_listings.filter(channel=channel_USD).update(
        price_amount=None, discounted_price_amount=None
    )
    listing = variant.channel_listings.get(channel=channel_USD)
    assert listing.is_available_for_purchase is True

    variables = {
        "slug": product_with_two_variants.slug,
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    returned_ids = {node["id"] for node in content["data"]["product"]["variants"]}
    assert graphene.Node.to_global_id("ProductVariant", variant.pk) not in returned_ids


def test_checkout_complete_rejects_the_variant(api_client, checkout_with_item):
    # given
    mutation = """
        mutation CheckoutComplete($id: ID) {
            checkoutComplete(id: $id) {
                order {
                    id
                }
                errors {
                    field
                    code
                    message
                    variants
                }
            }
        }
    """
    line = checkout_with_item.lines.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant_id)
    listing = line.variant.channel_listings.get(channel=checkout_with_item.channel)
    listing.is_available_for_purchase = False
    listing.save(update_fields=("is_available_for_purchase",))
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout_with_item.pk)}

    # when
    response = api_client.post_graphql(mutation, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutComplete"]
    assert data["order"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "lines"
    assert (
        data["errors"][0]["code"]
        == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    )
    assert data["errors"][0]["variants"] == [variant_id]
    assert Order.objects.exists() is False


def test_order_lines_create_rejects_the_variant(
    staff_api_client, draft_order, unavailable_variant, permission_group_manage_orders
):
    # given
    mutation = """
        mutation OrderLinesCreate($id: ID!, $input: [OrderLineCreateInput!]!) {
            orderLinesCreate(id: $id, input: $input) {
                errors {
                    field
                    code
                    message
                    variants
                }
                orderLines {
                    id
                }
            }
        }
    """
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    lines_count = draft_order.lines.count()
    variant_id = graphene.Node.to_global_id("ProductVariant", unavailable_variant.pk)
    variables = {
        "id": graphene.Node.to_global_id("Order", draft_order.pk),
        "input": [{"variantId": variant_id, "quantity": 1}],
    }

    # when
    response = staff_api_client.post_graphql(mutation, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "input"
    assert data["errors"][0]["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert data["errors"][0]["variants"] == [variant_id]
    assert draft_order.lines.count() == lines_count


def test_unavailable_gift_is_not_added_to_the_checkout(
    checkout_info, checkout_lines_info, gift_promotion_rule, channel_USD
):
    # given
    ProductVariantChannelListing.objects.filter(
        variant__in=gift_promotion_rule.gifts.all(), channel=channel_USD
    ).update(is_available_for_purchase=False)
    lines_count = len(checkout_lines_info)

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    checkout = checkout_info.checkout
    assert checkout.lines.filter(is_gift=True).exists() is False
    assert checkout.lines.count() == lines_count
    assert len(checkout_lines_info) == lines_count
