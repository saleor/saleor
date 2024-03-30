from datetime import datetime, timedelta

import graphene
import pytz

from .....checkout.error_codes import CheckoutCreateFromOrderUnavailableVariantErrorCode
from .....checkout.models import Checkout
from .....product.models import ProductVariantChannelListing
from .....warehouse.models import Stock
from ....tests.utils import get_graphql_content
from ...enums import CheckoutCreateFromOrderErrorCode

MUTATION_CHECKOUT_CREATE_FROM_ORDER = """
mutation CheckoutCreateFromOrder($id: ID!) {
  checkoutCreateFromOrder(id:$id){
    errors{
      field
      message
      code
    }
    unavailableVariants{
      message
      code
      variantId
      lineId
    }
    checkout{
      id
      lines{
        isGift
        quantity
        variant{
          id
        }
      }
    }
  }
}
"""


def _assert_checkout_lines(
    order_lines_map, checkout_lines, checkout_lines_from_response_map
):
    for line in checkout_lines:
        order_line = order_lines_map.get(line.variant.pk)
        assert line.quantity == order_line.quantity
        assert line.variant_id == order_line.variant_id
        variant_global_id = graphene.Node.to_global_id(
            "ProductVariant", line.variant.pk
        )
        line_from_response = checkout_lines_from_response_map.get(variant_global_id)
        assert line.quantity == line_from_response["quantity"]
        assert variant_global_id == line_from_response["variant"]["id"]


def test_checkout_create_from_order_with_same_user(user_api_client, order_with_lines):
    # given
    order_with_lines.user = user_api_client.user
    order_with_lines.save()
    Stock.objects.update(quantity=10)

    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    order_lines_map = {line.variant.pk: line for line in order_with_lines.lines.all()}

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    assert checkout.user == order_with_lines.user
    assert checkout.email == order_with_lines.user_email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert len(checkout_lines_from_response) == checkout_lines.count()
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }
    assert not data["unavailableVariants"]
    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )


def test_checkout_create_from_order_with_different_user(
    user_api_client, order_with_lines, customer_user2
):
    # given
    order_with_lines.user = customer_user2
    order_with_lines.save()
    assert user_api_client.user != customer_user2
    Stock.objects.update(quantity=10)

    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    order_lines_map = {line.variant.pk: line for line in order_with_lines.lines.all()}

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    assert checkout.user == user_api_client.user
    assert checkout.email == user_api_client.user.email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert len(checkout_lines_from_response) == checkout_lines.count()
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }
    assert not data["unavailableVariants"]
    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )


def test_checkout_create_from_order_with_anonymous_user(api_client, order_with_lines):
    # given
    Stock.objects.update(quantity=10)
    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables)

    # then
    order_lines_map = {line.variant.pk: line for line in order_with_lines.lines.all()}

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    assert not checkout.user
    assert not checkout.email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert len(checkout_lines_from_response) == checkout_lines.count()
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }
    assert not data["unavailableVariants"]
    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )


def test_checkout_create_from_anonymous_order_and_logged_in_user(
    user_api_client,
    order_with_lines,
):
    # given
    order_with_lines.user = None
    order_with_lines.save()
    Stock.objects.update(quantity=10)

    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    order_lines_map = {line.variant.pk: line for line in order_with_lines.lines.all()}

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    assert checkout.user == user_api_client.user
    assert checkout.email == user_api_client.user.email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert len(checkout_lines_from_response) == checkout_lines.count()
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }
    assert not data["unavailableVariants"]
    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )


def test_checkout_create_from_order_with_gift_reward(
    user_api_client, order_with_lines, gift_promotion_rule
):
    # given
    order_with_lines.user = user_api_client.user
    order_with_lines.save()

    order_lines_count = order_with_lines.lines.count()

    Stock.objects.update(quantity=10)

    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    variants = gift_promotion_rule.gifts.all()
    variant_listings = ProductVariantChannelListing.objects.filter(variant__in=variants)
    top_price, variant_id = max(
        variant_listings.values_list("discounted_price_amount", "variant")
    )
    order_lines_map = {line.variant.pk: line for line in order_with_lines.lines.all()}

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    gift_line = checkout_lines.filter(is_gift=True).first()
    order_lines_map[variant_id] = gift_line
    assert checkout.user == order_with_lines.user
    assert checkout.email == order_with_lines.user_email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert (
        len(checkout_lines_from_response)
        == checkout_lines.count()
        == order_lines_count + 1
    )
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }
    assert not data["unavailableVariants"]
    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )
    assert gift_line.discounts.count() == 1
    discount = gift_line.discounts.first()
    gift_variant_listing = gift_line.variant.channel_listings.get(
        channel=checkout.channel
    )
    assert discount.amount_value == gift_variant_listing.price_amount


def test_checkout_create_from_order_when_order_not_found(
    user_api_client,
    order_with_lines,
):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    order_with_lines.delete()
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["checkoutCreateFromOrder"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "id"
    assert error["code"] == CheckoutCreateFromOrderErrorCode.ORDER_NOT_FOUND.name


def test_checkout_create_from_order_variant_not_found(
    user_api_client, order_with_lines
):
    # given
    order_with_lines.user = user_api_client.user
    order_with_lines.save()
    Stock.objects.update(quantity=10)
    first_line = order_with_lines.lines.first()
    first_line.variant.delete()

    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    order_lines_map = {
        line.variant.pk: line for line in order_with_lines.lines.all() if line.variant
    }

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    assert checkout.user == order_with_lines.user
    assert checkout.email == order_with_lines.user_email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert (
        len(checkout_lines_from_response)
        == checkout_lines.count()
        == len(order_lines_map)
    )
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }

    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )

    error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
    assert len(data["unavailableVariants"]) == 1
    unavailable_variant = data["unavailableVariants"][0]
    assert unavailable_variant["code"] == error_codes.NOT_FOUND.name
    assert unavailable_variant["lineId"] == graphene.Node.to_global_id(
        "OrderLine", first_line.pk
    )
    assert unavailable_variant["variantId"] == first_line.product_variant_id


def test_checkout_create_from_order_variant_not_available_in_channel(
    user_api_client, order_with_lines
):
    # given
    order_with_lines.user = user_api_client.user
    order_with_lines.save()
    Stock.objects.update(quantity=10)
    first_line = order_with_lines.lines.first()
    first_line.variant.channel_listings.all().delete()

    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    order_lines_map = {line.variant.pk: line for line in order_with_lines.lines.all()}

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    assert checkout.user == order_with_lines.user
    assert checkout.email == order_with_lines.user_email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert (
        len(checkout_lines_from_response)
        == checkout_lines.count()
        == len(order_lines_map) - 1
    )
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }

    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )

    error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
    assert len(data["unavailableVariants"]) == 1
    unavailable_variant = data["unavailableVariants"][0]
    assert (
        unavailable_variant["code"] == error_codes.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    )
    assert unavailable_variant["lineId"] == graphene.Node.to_global_id(
        "OrderLine", first_line.pk
    )
    assert unavailable_variant["variantId"] == first_line.product_variant_id


def test_checkout_create_from_order_variant_not_published(
    user_api_client, order_with_lines
):
    # given
    order_with_lines.user = user_api_client.user
    order_with_lines.save()
    Stock.objects.update(quantity=10)
    first_line = order_with_lines.lines.first()
    first_line.variant.product.channel_listings.all().update(is_published=False)

    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    order_lines_map = {line.variant.pk: line for line in order_with_lines.lines.all()}

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    assert checkout.user == order_with_lines.user
    assert checkout.email == order_with_lines.user_email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert (
        len(checkout_lines_from_response)
        == checkout_lines.count()
        == len(order_lines_map) - 1
    )
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }

    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )

    error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
    assert len(data["unavailableVariants"]) == 1
    unavailable_variant = data["unavailableVariants"][0]
    assert unavailable_variant["code"] == error_codes.PRODUCT_NOT_PUBLISHED.name
    assert unavailable_variant["lineId"] == graphene.Node.to_global_id(
        "OrderLine", first_line.pk
    )
    assert unavailable_variant["variantId"] == first_line.product_variant_id


def test_checkout_create_from_order_variant_exceed_variant_quantity_limit(
    user_api_client, order_with_lines
):
    # given
    order_with_lines.user = user_api_client.user
    order_with_lines.save()
    Stock.objects.update(quantity=10)
    first_line = order_with_lines.lines.first()
    variant = first_line.variant
    variant.quantity_limit_per_customer = first_line.quantity - 1
    variant.save()

    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    order_lines_map = {line.variant.pk: line for line in order_with_lines.lines.all()}

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    assert checkout.user == order_with_lines.user
    assert checkout.email == order_with_lines.user_email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert (
        len(checkout_lines_from_response)
        == checkout_lines.count()
        == len(order_lines_map) - 1
    )
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }

    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )

    error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
    assert len(data["unavailableVariants"]) == 1
    unavailable_variant = data["unavailableVariants"][0]
    assert unavailable_variant["code"] == error_codes.QUANTITY_GREATER_THAN_LIMIT.name
    assert unavailable_variant["lineId"] == graphene.Node.to_global_id(
        "OrderLine", first_line.pk
    )
    assert unavailable_variant["variantId"] == first_line.product_variant_id


def test_checkout_create_from_order_variant_exceed_global_quantity_limit(
    user_api_client, order_with_lines, site_settings
):
    # given
    order_with_lines.user = user_api_client.user
    order_with_lines.save()
    Stock.objects.update(quantity=10)
    first_line = order_with_lines.lines.first()
    first_line.quantity = 25
    first_line.save()

    site_settings.limit_quantity_per_checkout = 20
    site_settings.save()

    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    order_lines_map = {line.variant.pk: line for line in order_with_lines.lines.all()}

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    assert checkout.user == order_with_lines.user
    assert checkout.email == order_with_lines.user_email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert (
        len(checkout_lines_from_response)
        == checkout_lines.count()
        == len(order_lines_map) - 1
    )
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }

    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )

    error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
    assert len(data["unavailableVariants"]) == 1
    unavailable_variant = data["unavailableVariants"][0]
    assert unavailable_variant["code"] == error_codes.QUANTITY_GREATER_THAN_LIMIT.name
    assert unavailable_variant["lineId"] == graphene.Node.to_global_id(
        "OrderLine", first_line.pk
    )
    assert unavailable_variant["variantId"] == first_line.product_variant_id


def test_checkout_create_from_order_variant_not_available_for_purchase(
    user_api_client, order_with_lines
):
    # given
    available_at = datetime.now(pytz.UTC) + timedelta(days=2)
    order_with_lines.user = user_api_client.user
    order_with_lines.save()
    Stock.objects.update(quantity=10)
    first_line = order_with_lines.lines.first()
    first_line.variant.product.channel_listings.all().update(
        available_for_purchase_at=available_at
    )

    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    order_lines_map = {line.variant.pk: line for line in order_with_lines.lines.all()}

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    assert checkout.user == order_with_lines.user
    assert checkout.email == order_with_lines.user_email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert (
        len(checkout_lines_from_response)
        == checkout_lines.count()
        == len(order_lines_map) - 1
    )
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }

    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )

    error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
    assert len(data["unavailableVariants"]) == 1
    unavailable_variant = data["unavailableVariants"][0]
    assert (
        unavailable_variant["code"] == error_codes.PRODUCT_UNAVAILABLE_FOR_PURCHASE.name
    )
    assert unavailable_variant["lineId"] == graphene.Node.to_global_id(
        "OrderLine", first_line.pk
    )
    assert unavailable_variant["variantId"] == first_line.product_variant_id


def test_checkout_create_from_order_variant_out_of_stock(
    user_api_client, order_with_lines
):
    # given
    order_with_lines.user = user_api_client.user
    order_with_lines.save()
    first_line = order_with_lines.lines.first()
    Stock.objects.exclude(product_variant=first_line.variant).update(quantity=10)

    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    order_lines_map = {line.variant.pk: line for line in order_with_lines.lines.all()}

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    assert checkout.user == order_with_lines.user
    assert checkout.email == order_with_lines.user_email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert (
        len(checkout_lines_from_response)
        == checkout_lines.count()
        == len(order_lines_map) - 1
    )
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }

    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )

    error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
    assert len(data["unavailableVariants"]) == 1
    unavailable_variant = data["unavailableVariants"][0]
    assert unavailable_variant["code"] == error_codes.INSUFFICIENT_STOCK.name
    assert unavailable_variant["lineId"] == graphene.Node.to_global_id(
        "OrderLine", first_line.pk
    )
    assert unavailable_variant["variantId"] == first_line.product_variant_id


def test_checkout_create_from_order_variant_not_enough_stock(
    user_api_client, order_with_lines
):
    # given
    order_with_lines.user = user_api_client.user
    order_with_lines.save()
    first_line = order_with_lines.lines.first()
    Stock.objects.exclude(product_variant=first_line.variant).update(quantity=10)
    Stock.objects.filter(product_variant=first_line.variant).update(
        quantity=first_line.quantity - 1
    )

    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    order_lines_map = {line.variant.pk: line for line in order_with_lines.lines.all()}

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    assert checkout.user == order_with_lines.user
    assert checkout.email == order_with_lines.user_email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert (
        len(checkout_lines_from_response)
        == checkout_lines.count()
        == len(order_lines_map) - 1
    )
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }

    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )

    error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
    assert len(data["unavailableVariants"]) == 1
    unavailable_variant = data["unavailableVariants"][0]
    assert unavailable_variant["code"] == error_codes.INSUFFICIENT_STOCK.name
    assert unavailable_variant["lineId"] == graphene.Node.to_global_id(
        "OrderLine", first_line.pk
    )
    assert unavailable_variant["variantId"] == first_line.product_variant_id


def test_checkout_create_from_order_multiple_unavailable_variants(
    user_api_client, order_with_lines, order_line
):
    # given
    order_with_lines.user = user_api_client.user
    order_with_lines.save()
    order_line.order_id = order_with_lines.pk
    order_line.save()
    first_line = order_with_lines.lines.first()

    Stock.objects.exclude(product_variant=first_line.variant).update(quantity=10)
    order_line.variant.channel_listings.all().delete()

    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    order_lines_map = {line.variant.pk: line for line in order_with_lines.lines.all()}

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    assert checkout.user == order_with_lines.user
    assert checkout.email == order_with_lines.user_email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert (
        len(checkout_lines_from_response)
        == checkout_lines.count()
        == len(order_lines_map) - 2
    )
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }

    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )

    error_codes = CheckoutCreateFromOrderUnavailableVariantErrorCode
    assert len(data["unavailableVariants"]) == 2

    unavailable_variants = data["unavailableVariants"]
    errors = {variant_data["code"] for variant_data in unavailable_variants}
    line_ids = {variant_data["lineId"] for variant_data in unavailable_variants}
    variant_ids = {variant_data["variantId"] for variant_data in unavailable_variants}
    assert errors == {
        error_codes.INSUFFICIENT_STOCK.name,
        error_codes.UNAVAILABLE_VARIANT_IN_CHANNEL.name,
    }
    assert line_ids == {
        graphene.Node.to_global_id("OrderLine", first_line.pk),
        graphene.Node.to_global_id("OrderLine", order_line.pk),
    }
    assert variant_ids == {first_line.product_variant_id, order_line.product_variant_id}


def test_checkout_create_from_order_with_the_same_variant_in_multiple_lines(
    user_api_client, order_with_lines
):
    # given
    order_with_lines.user = user_api_client.user
    order_with_lines.save()
    Stock.objects.update(quantity=10)
    first_line = order_with_lines.lines.first()
    first_line.pk = None
    first_line.save()

    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE_FROM_ORDER, variables
    )

    # then
    order_lines_map = {line.variant.pk: line for line in order_with_lines.lines.all()}

    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    checkout = Checkout.objects.get()
    checkout_lines = checkout.lines.all()
    assert checkout.user == order_with_lines.user
    assert checkout.email == order_with_lines.user_email
    checkout_lines_from_response = data["checkout"]["lines"]
    assert (
        len(checkout_lines_from_response)
        == checkout_lines.count()
        == order_with_lines.lines.count()
    )
    checkout_lines_from_response_map = {
        line["variant"]["id"]: line for line in checkout_lines_from_response
    }
    assert not data["unavailableVariants"]
    assert data["checkout"]["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    _assert_checkout_lines(
        order_lines_map, checkout_lines, checkout_lines_from_response_map
    )
