from datetime import timedelta

import graphene
from django.utils import timezone

from ...tests.utils import get_graphql_content

QUERY_CHECKOUT_BASIC_FIELDS = """
query getCheckout($id: ID) {
  checkout(id: $id) {
    id
    token
    email
  }
}
"""


QUERY_CHECKOUT_LINES_ONLY_ID = """
query getCheckout($id: ID) {
  checkout(id: $id) {
    token
    lines {
      id
      isGift
    }
  }
}
"""


QUERY_CHECKOUT_LINES_WITH_PRICES = """
query getCheckout($id: ID) {
  checkout(id: $id) {
    token
    lines {
      id
      isGift
      quantity
      variant {
        id
      }
      unitPrice {
        gross {
          amount
        }
      }
      totalPrice {
        currency
        gross {
          amount
        }
      }
      undiscountedUnitPrice {
        amount
        currency
      }
      undiscountedTotalPrice {
        amount
        currency
      }
    }
  }
}
"""


def test_checkout_basic_fields_no_recalculation(
    user_api_client, checkout_with_item_and_gift_promotion, gift_promotion_rule, product
):
    """Test that querying only basic checkout fields performs NO recalculation.

    This test ensures that when querying only basic fields (id, token, email)
    that don't involve lines or pricing, the system will:
    1. NOT recalculate discounts (keep discount_price_expiration unchanged)
    2. NOT recalculate taxes (keep price_expiration unchanged)
    3. Return data without triggering any expensive calculations
    """
    # given
    checkout = checkout_with_item_and_gift_promotion
    query = QUERY_CHECKOUT_BASIC_FIELDS

    initial_price_expiration = timezone.now() - timedelta(minutes=5)
    initial_discount_price_expiration = timezone.now() - timedelta(minutes=5)
    checkout.price_expiration = initial_price_expiration
    checkout.discount_price_expiration = initial_discount_price_expiration
    checkout.save(update_fields=["price_expiration", "discount_price_expiration"])

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    # Change gift promotion to simulate that data is stale
    new_gift_variant = product.variants.last()
    gift_promotion_rule.gifts.set([new_gift_variant])
    gift_promotion_rule.order_predicate = {"discountedObjectPredicate": {}}
    gift_promotion_rule.save(update_fields=["order_predicate"])

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    assert data["token"] == str(checkout.token)
    assert data["email"] == checkout.email

    checkout.refresh_from_db()
    # Verify that NO recalculation happened - both expirations should remain unchanged
    assert checkout.discount_price_expiration == initial_discount_price_expiration
    assert checkout.price_expiration == initial_price_expiration


def test_checkout_gift_promotion_changed_only_line_id(
    user_api_client, checkout_with_item_and_gift_promotion, gift_promotion_rule, product
):
    """Test that querying only line.id triggers discount recalculation but NOT tax recalculation.

    This test ensures that when a gift promotion changes and we only query line IDs,
    the system will:
    1. Recalculate discounts (update discount_price_expiration)
    2. Update gift lines to reflect the new promotion
    3. NOT recalculate taxes (keep price_expiration unchanged)

    This prevents unnecessary expensive tax calculations when only IDs are needed.
    """
    # given
    checkout = checkout_with_item_and_gift_promotion
    query = QUERY_CHECKOUT_LINES_ONLY_ID

    initial_price_expiration = timezone.now() - timedelta(minutes=5)
    checkout.price_expiration = initial_price_expiration
    checkout.discount_price_expiration = initial_price_expiration
    checkout.save(update_fields=["price_expiration", "discount_price_expiration"])

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    lines_count = checkout.lines.count()

    # Get initial gift line
    initial_gift_line = checkout.lines.filter(is_gift=True).first()
    initial_gift_line_variant = initial_gift_line.variant
    assert initial_gift_line is not None

    # Change gift promotion to a different variant
    new_gift_variant = product.variants.last()
    gift_promotion_rule.gifts.set([new_gift_variant])
    gift_promotion_rule.order_predicate = {"discountedObjectPredicate": {}}
    gift_promotion_rule.save(update_fields=["order_predicate"])

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == lines_count

    # Verify the gift line was updated to the new variant
    gift_line = checkout.lines.filter(is_gift=True).first()
    assert gift_line.variant != initial_gift_line_variant
    assert gift_line.variant == new_gift_variant

    # Verify the response contains the updated gift line
    gift_lines = [line for line in data["lines"] if line["isGift"] is True]
    assert len(gift_lines) == 1

    gift_line_data = gift_lines[0]
    assert gift_line_data["id"] == graphene.Node.to_global_id(
        "CheckoutLine", gift_line.pk
    )

    # Verify discount_price_expiration was updated (discount recalculation happened)
    checkout.refresh_from_db()
    assert checkout.discount_price_expiration > timezone.now()

    # Verify price_expiration was NOT updated (tax recalculation did NOT happen)
    assert checkout.price_expiration == initial_price_expiration


def test_checkout_gift_promotion_changed_with_line_prices(
    user_api_client, checkout_with_item_and_gift_promotion, gift_promotion_rule, product
):
    """Test that querying line prices triggers both discount and tax recalculation.

    This test ensures that when a gift promotion changes and we query line prices,
    the system will:
    1. Recalculate discounts (update discount_price_expiration)
    2. Update gift lines to reflect the new promotion
    3. Recalculate taxes (update price_expiration)
    4. Return correct pricing for gift lines (unit price = 0, undiscounted price > 0)

    This ensures accurate pricing information when price fields are requested.
    """
    # given
    checkout = checkout_with_item_and_gift_promotion
    query = QUERY_CHECKOUT_LINES_WITH_PRICES

    initial_price_expiration = timezone.now() - timedelta(minutes=5)
    checkout.price_expiration = initial_price_expiration
    checkout.discount_price_expiration = initial_price_expiration
    checkout.save(update_fields=["price_expiration", "discount_price_expiration"])

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    lines_count = checkout.lines.count()

    # Get initial gift line
    initial_gift_line = checkout.lines.filter(is_gift=True).first()
    initial_gift_line_variant = initial_gift_line.variant
    assert initial_gift_line is not None

    # Change gift promotion to a different variant
    new_gift_variant = product.variants.last()
    gift_promotion_rule.gifts.set([new_gift_variant])
    gift_promotion_rule.order_predicate = {"discountedObjectPredicate": {}}
    gift_promotion_rule.save(update_fields=["order_predicate"])

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)
    assert len(data["lines"]) == lines_count

    # Verify the gift line was updated to the new variant
    gift_line = checkout.lines.filter(is_gift=True).first()
    assert gift_line.variant != initial_gift_line_variant
    assert gift_line.variant == new_gift_variant

    # Verify the response contains the updated gift line
    gift_lines = [line for line in data["lines"] if line["isGift"] is True]
    assert len(gift_lines) == 1

    gift_line_data = gift_lines[0]
    assert gift_line_data["id"] == graphene.Node.to_global_id(
        "CheckoutLine", gift_line.pk
    )

    # Verify gift line has correct pricing
    assert gift_line_data["unitPrice"]["gross"]["amount"] == 0
    assert gift_line_data["totalPrice"]["gross"]["amount"] == 0
    # undiscountedUnitPrice should have the original price of the variant
    assert gift_line_data["undiscountedUnitPrice"]["amount"] > 0

    # Verify both expirations were updated (full recalculation happened)
    checkout.refresh_from_db()
    assert checkout.discount_price_expiration > timezone.now()
    assert checkout.price_expiration > timezone.now()


def test_checkout_gift_promotion_removed_only_line_id(
    user_api_client, checkout_with_item_and_gift_promotion, gift_promotion_rule
):
    """Test that querying only line.id triggers discount recalculation when gift promotion is removed.

    This test ensures that when a gift promotion is removed and we only query line IDs,
    the system will:
    1. Recalculate discounts (update discount_price_expiration)
    2. Remove gift lines that are no longer valid
    3. NOT recalculate taxes (keep price_expiration unchanged)

    This prevents unnecessary expensive tax calculations when only IDs are needed.
    """
    # given
    checkout = checkout_with_item_and_gift_promotion
    query = QUERY_CHECKOUT_LINES_ONLY_ID

    initial_price_expiration = timezone.now() - timedelta(minutes=5)
    checkout.price_expiration = initial_price_expiration
    checkout.discount_price_expiration = initial_price_expiration
    checkout.save(update_fields=["price_expiration", "discount_price_expiration"])

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    initial_lines_count = checkout.lines.count()
    initial_gift_line = checkout.lines.filter(is_gift=True).first()
    assert initial_gift_line is not None

    # Remove the gift promotion
    gift_promotion_rule.delete()

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)

    # Gift line should be removed
    assert len(data["lines"]) == initial_lines_count - 1

    # Verify no gift lines remain
    gift_lines = [line for line in data["lines"] if line["isGift"] is True]
    assert len(gift_lines) == 0

    # Verify gift line was removed from database
    gift_line_exists = checkout.lines.filter(is_gift=True).exists()
    assert not gift_line_exists

    # Verify discount_price_expiration was updated (discount recalculation happened)
    checkout.refresh_from_db()
    assert checkout.discount_price_expiration > timezone.now()

    # Verify price_expiration was NOT updated (tax recalculation did NOT happen)
    assert checkout.price_expiration == initial_price_expiration


def test_checkout_gift_promotion_removed_with_line_prices(
    user_api_client, checkout_with_item_and_gift_promotion, gift_promotion_rule
):
    """Test that querying line prices triggers both discount and tax recalculation when gift promotion is removed.

    This test ensures that when a gift promotion is removed and we query line prices,
    the system will:
    1. Recalculate discounts (update discount_price_expiration)
    2. Remove gift lines that are no longer valid
    3. Recalculate taxes (update price_expiration)

    This ensures accurate pricing information when price fields are requested.
    """
    # given
    checkout = checkout_with_item_and_gift_promotion
    query = QUERY_CHECKOUT_LINES_WITH_PRICES

    initial_price_expiration = timezone.now() - timedelta(minutes=5)
    checkout.price_expiration = initial_price_expiration
    checkout.discount_price_expiration = initial_price_expiration
    checkout.save(update_fields=["price_expiration", "discount_price_expiration"])

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    initial_lines_count = checkout.lines.count()
    initial_gift_line = checkout.lines.filter(is_gift=True).first()
    assert initial_gift_line is not None

    # Remove the gift promotion
    gift_promotion_rule.delete()

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)

    # Gift line should be removed
    assert len(data["lines"]) == initial_lines_count - 1

    # Verify no gift lines remain
    gift_lines = [line for line in data["lines"] if line["isGift"] is True]
    assert len(gift_lines) == 0

    # Verify gift line was removed from database
    gift_line_exists = checkout.lines.filter(is_gift=True).exists()
    assert not gift_line_exists

    # Verify both expirations were updated (full recalculation happened)
    checkout.refresh_from_db()
    assert checkout.discount_price_expiration > timezone.now()
    assert checkout.price_expiration > timezone.now()


def test_checkout_gift_promotion_added_only_line_id(
    user_api_client, checkout_with_item, gift_promotion_rule, product
):
    """Test that querying only line.id triggers discount recalculation when gift promotion is added.

    This test ensures that when a gift promotion is added to a checkout without gift lines
    and we only query line IDs, the system will:
    1. Recalculate discounts (update discount_price_expiration)
    2. Add new gift lines based on the promotion
    3. NOT recalculate taxes (keep price_expiration unchanged)

    This prevents unnecessary expensive tax calculations when only IDs are needed.
    """
    # given
    checkout = checkout_with_item
    query = QUERY_CHECKOUT_LINES_ONLY_ID

    initial_price_expiration = timezone.now() - timedelta(minutes=5)
    checkout.price_expiration = initial_price_expiration
    checkout.discount_price_expiration = initial_price_expiration
    checkout.save(update_fields=["price_expiration", "discount_price_expiration"])

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    initial_lines_count = checkout.lines.count()

    # Verify no gift lines initially exist
    initial_gift_line = checkout.lines.filter(is_gift=True).first()
    assert initial_gift_line is None

    # Add gift to the promotion rule
    gift_variant = product.variants.first()
    gift_promotion_rule.gifts.set([gift_variant])
    gift_promotion_rule.order_predicate = {"discountedObjectPredicate": {}}
    gift_promotion_rule.save(update_fields=["order_predicate"])

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)

    # Gift line should be added
    assert len(data["lines"]) == initial_lines_count + 1

    # Verify gift line was added
    gift_lines = [line for line in data["lines"] if line["isGift"] is True]
    assert len(gift_lines) == 1

    # Verify gift line exists in database
    gift_line = checkout.lines.filter(is_gift=True).first()
    assert gift_line is not None
    assert gift_line.variant == gift_variant

    # Verify the response contains the added gift line
    gift_line_data = gift_lines[0]
    assert gift_line_data["id"] == graphene.Node.to_global_id(
        "CheckoutLine", gift_line.pk
    )

    # Verify discount_price_expiration was updated (discount recalculation happened)
    checkout.refresh_from_db()
    assert checkout.discount_price_expiration > timezone.now()

    # Verify price_expiration was NOT updated (tax recalculation did NOT happen)
    assert checkout.price_expiration == initial_price_expiration


def test_checkout_gift_promotion_added_with_line_prices(
    user_api_client, checkout_with_item, gift_promotion_rule, product
):
    """Test that querying line prices triggers both discount and tax recalculation when gift promotion is added.

    This test ensures that when a gift promotion is added to a checkout without gift lines
    and we query line prices, the system will:
    1. Recalculate discounts (update discount_price_expiration)
    2. Add new gift lines based on the promotion
    3. Recalculate taxes (update price_expiration)
    4. Return correct pricing for gift lines (unit price = 0, undiscounted price > 0)

    This ensures accurate pricing information when price fields are requested.
    """
    # given
    checkout = checkout_with_item
    query = QUERY_CHECKOUT_LINES_WITH_PRICES

    initial_price_expiration = timezone.now() - timedelta(minutes=5)
    checkout.price_expiration = initial_price_expiration
    checkout.discount_price_expiration = initial_price_expiration
    checkout.save(update_fields=["price_expiration", "discount_price_expiration"])

    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    initial_lines_count = checkout.lines.count()

    # Verify no gift lines initially exist
    initial_gift_line = checkout.lines.filter(is_gift=True).first()
    assert initial_gift_line is None

    # Add gift to the promotion rule
    gift_variant = product.variants.first()
    gift_promotion_rule.gifts.set([gift_variant])
    gift_promotion_rule.order_predicate = {"discountedObjectPredicate": {}}
    gift_promotion_rule.save(update_fields=["order_predicate"])

    # when
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["token"] == str(checkout.token)

    # Gift line should be added
    assert len(data["lines"]) == initial_lines_count + 1

    # Verify gift line was added
    gift_lines = [line for line in data["lines"] if line["isGift"] is True]
    assert len(gift_lines) == 1

    # Verify gift line exists in database
    gift_line = checkout.lines.filter(is_gift=True).first()
    assert gift_line is not None
    assert gift_line.variant == gift_variant

    # Verify the response contains the added gift line
    gift_line_data = gift_lines[0]
    assert gift_line_data["id"] == graphene.Node.to_global_id(
        "CheckoutLine", gift_line.pk
    )

    # Verify gift line has correct pricing
    assert gift_line_data["unitPrice"]["gross"]["amount"] == 0
    assert gift_line_data["totalPrice"]["gross"]["amount"] == 0
    # undiscountedUnitPrice should have the original price of the variant
    assert gift_line_data["undiscountedUnitPrice"]["amount"] > 0

    # Verify both expirations were updated (full recalculation happened)
    checkout.refresh_from_db()
    assert checkout.discount_price_expiration > timezone.now()
    assert checkout.price_expiration > timezone.now()
