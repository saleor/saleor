from decimal import Decimal

import graphene

from ....product.models import Product
from ....product.utils.variant_prices import update_discounted_prices_for_promotion
from ...core.utils import to_global_id_or_none
from ...tests.utils import get_graphql_content

QUERY_CHECKOUT_LINE_PRICES = """
query getCheckout($id: ID) {
  checkout(id: $id) {
    lines {
      undiscountedUnitPrice {
        amount
      }
      unitPrice {
        net {
          amount
        }
      }
      totalPrice {
        net {
          amount
        }
      }
    }
    subtotalPrice {
      net {
        amount
      }
    }
  }
}
"""


def test_checkout_line_prices_apply_the_buyer_rule_of_the_customer(
    user_api_client,
    b2b_customer_user,
    checkout_with_item,
    product,
    catalogue_promotion,
    promotion_rule_for_customer_type,
):
    # given
    # the public 10% rule is stored, the 25% B2B rule is resolved per buyer
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))
    checkout = checkout_with_item
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    line = checkout.lines.get()
    assert line.variant.product_id == product.pk
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = user_api_client.post_graphql(QUERY_CHECKOUT_LINE_PRICES, variables)

    # then
    data = get_graphql_content(response)["data"]["checkout"]
    [line_data] = data["lines"]
    assert line_data["undiscountedUnitPrice"]["amount"] == 10
    assert line_data["unitPrice"]["net"]["amount"] == 7.5
    assert line_data["totalPrice"]["net"]["amount"] == 7.5 * line.quantity
    assert data["subtotalPrice"]["net"]["amount"] == 7.5 * line.quantity
    line.refresh_from_db(fields=["quantity"])
    discount = line.discounts.get()
    assert discount.promotion_rule == promotion_rule_for_customer_type
    assert discount.amount_value == Decimal("2.50") * line.quantity


def test_checkout_line_prices_keep_the_stored_rule_for_a_guest(
    api_client,
    checkout_with_item,
    product,
    catalogue_promotion,
    promotion_rule_for_customer_type,
):
    # given
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))
    checkout = checkout_with_item
    assert checkout.user is None
    line = checkout.lines.get()
    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_LINE_PRICES, variables)

    # then
    data = get_graphql_content(response)["data"]["checkout"]
    [line_data] = data["lines"]
    assert line_data["undiscountedUnitPrice"]["amount"] == 10
    assert line_data["unitPrice"]["net"]["amount"] == 9
    discount = line.discounts.get()
    assert discount.promotion_rule == catalogue_promotion.rules.get(
        reward_value=Decimal(10)
    )


MUTATION_CHECKOUT_LINES_ADD = """
mutation checkoutLinesAdd($id: ID, $lines: [CheckoutLineInput!]!) {
  checkoutLinesAdd(id: $id, lines: $lines) {
    checkout {
      lines {
        unitPrice {
          net {
            amount
          }
        }
      }
    }
    errors {
      field
      code
    }
  }
}
"""


def test_checkout_lines_add_applies_the_buyer_rule_of_the_customer(
    user_api_client,
    b2b_customer_user,
    checkout,
    variant,
    stock,
    product,
    catalogue_promotion,
    promotion_rule_for_customer_type,
):
    # given
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))
    checkout.user = b2b_customer_user
    checkout.save(update_fields=["user"])
    variables = {
        "id": to_global_id_or_none(checkout),
        "lines": [
            {
                "variantId": graphene.Node.to_global_id("ProductVariant", variant.pk),
                "quantity": 1,
            }
        ],
    }

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)

    # then
    data = get_graphql_content(response)["data"]["checkoutLinesAdd"]
    assert data["errors"] == []
    [line_data] = data["checkout"]["lines"]
    assert line_data["unitPrice"]["net"]["amount"] == 7.5
    line = checkout.lines.get()
    assert line.discounts.get().promotion_rule == promotion_rule_for_customer_type
