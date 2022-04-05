from ....discount import DiscountType, DiscountValueType
from ...tests.utils import assert_no_permission, get_graphql_content

CHECKOUT_DISCOUNTS_FOR_CUSTOMERS_QUERY = """
query getCheckout($token: UUID) {
  checkout(token: $token) {
    discounts {
      type
      name
      translatedName
      valueType
      value
      amount {
        amount
      }
    }
  }
}
"""


def test_checkout_fixed_discount_as_customer(api_client, checkout_with_fixed_discount):
    # given
    checkout = checkout_with_fixed_discount
    discount = checkout.discounts.get()
    variables = {"token": str(checkout.token)}

    # when
    response = api_client.post_graphql(
        CHECKOUT_DISCOUNTS_FOR_CUSTOMERS_QUERY, variables
    )
    content = get_graphql_content(response)

    # then
    checkout_data = content["data"]["checkout"]
    discount_data = checkout_data["discounts"][0]

    assert discount_data["type"] == DiscountType.MANUAL.upper()
    assert discount_data["name"] == discount.name
    assert discount_data["translatedName"] == discount.translated_name
    assert discount_data["valueType"] == DiscountValueType.FIXED.upper()
    assert discount_data["value"] == discount.value
    assert discount_data["amount"]["amount"] == discount.amount.amount
    assert "reason" not in discount_data


def test_checkout_percentage_discount_as_customer(
    api_client, checkout_with_percentage_discount
):
    # given
    checkout = checkout_with_percentage_discount
    discount = checkout.discounts.get()
    variables = {"token": str(checkout.token)}

    # when
    response = api_client.post_graphql(
        CHECKOUT_DISCOUNTS_FOR_CUSTOMERS_QUERY, variables
    )
    content = get_graphql_content(response)

    # then
    checkout_data = content["data"]["checkout"]
    discount_data = checkout_data["discounts"][0]

    assert discount_data["type"] == DiscountType.MANUAL.upper()
    assert discount_data["name"] == discount.name
    assert discount_data["translatedName"] == discount.translated_name
    assert discount_data["valueType"] == DiscountValueType.PERCENTAGE.upper()
    assert discount_data["value"] == discount.value
    assert discount_data["amount"]["amount"] == discount.amount.amount
    assert "reason" not in discount_data


CHECKOUT_DISCOUNTS_FOR_ADMINS_QUERY = """
query getCheckout($token: UUID) {
  checkout(token: $token) {
    discounts {
      type
      name
      translatedName
      valueType
      value
      reason
      amount {
        amount
      }
    }
  }
}
"""


def test_checkout_fixed_discount_with_reason_as_customer(
    api_client, checkout_with_fixed_discount
):
    # given
    checkout = checkout_with_fixed_discount
    variables = {"token": str(checkout.token)}

    # when
    response = api_client.post_graphql(CHECKOUT_DISCOUNTS_FOR_ADMINS_QUERY, variables)

    # then
    assert_no_permission(response)


def test_checkout_fixed_discount_as_staff(
    staff_api_client, checkout_with_fixed_discount, permission_manage_checkouts
):
    # given
    checkout = checkout_with_fixed_discount
    discount = checkout.discounts.get()
    variables = {"token": str(checkout.token)}

    # when
    response = staff_api_client.post_graphql(
        CHECKOUT_DISCOUNTS_FOR_ADMINS_QUERY,
        variables,
        permissions=(permission_manage_checkouts,),
    )
    content = get_graphql_content(response)

    # then
    checkout_data = content["data"]["checkout"]
    discount_data = checkout_data["discounts"][0]

    assert discount_data["type"] == DiscountType.MANUAL.upper()
    assert discount_data["name"] == discount.name
    assert discount_data["translatedName"] == discount.translated_name
    assert discount_data["valueType"] == DiscountValueType.FIXED.upper()
    assert discount_data["value"] == discount.value
    assert discount_data["amount"]["amount"] == discount.amount.amount
    assert discount_data["reason"] == discount.reason


def test_checkout_percentage_discount_as_staff(
    staff_api_client, checkout_with_percentage_discount, permission_manage_checkouts
):
    # given
    checkout = checkout_with_percentage_discount
    discount = checkout.discounts.get()
    variables = {"token": str(checkout.token)}

    # when
    response = staff_api_client.post_graphql(
        CHECKOUT_DISCOUNTS_FOR_ADMINS_QUERY,
        variables,
        permissions=(permission_manage_checkouts,),
    )
    content = get_graphql_content(response)

    # then
    checkout_data = content["data"]["checkout"]
    discount_data = checkout_data["discounts"][0]

    assert discount_data["type"] == DiscountType.MANUAL.upper()
    assert discount_data["name"] == discount.name
    assert discount_data["translatedName"] == discount.translated_name
    assert discount_data["valueType"] == DiscountValueType.PERCENTAGE.upper()
    assert discount_data["value"] == discount.value
    assert discount_data["amount"]["amount"] == discount.amount.amount
    assert discount_data["reason"] == discount.reason


CHECKOUT_DISCOUNTS_CALCULATIONS_QUERY = """
query getCheckout($token: UUID) {
  checkout(token: $token) {
    lines {
      totalPrice {
        gross {
          amount
        }
      }
    }
    shippingPrice{
      gross{
        amount
      }
    }
    discounts{
      value
      amount{
        amount
      }
    }
    discount{
      amount
    }
    totalPrice {
      gross {
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
"""


def test_checkout_pricing_with_fixed_discount(
    api_client, checkout_with_fixed_discount, sale
):
    # given
    checkout = checkout_with_fixed_discount
    variables = {"token": str(checkout.token)}

    # when
    response = api_client.post_graphql(CHECKOUT_DISCOUNTS_CALCULATIONS_QUERY, variables)
    content = get_graphql_content(response)

    # then
    checkout_data = content["data"]["checkout"]
    discount_data = checkout_data["discounts"][0]
    checkout_total = checkout_data["totalPrice"]["gross"]["amount"]
    checkout_subtotal = checkout_data["subtotalPrice"]["gross"]["amount"]
    checkout_shipping_price = checkout_data["shippingPrice"]["gross"]["amount"]
    checkout_undiscounted_total = checkout_subtotal + checkout_shipping_price

    assert checkout_total > 0
    assert checkout_undiscounted_total > checkout_total
    assert discount_data["amount"]["amount"] + checkout_total == round(
        checkout_subtotal + checkout_shipping_price, 2
    )
    assert discount_data["amount"]["amount"] == discount_data["value"]


def test_checkout_pricing_with_fixed_discount_for_more_then_total(
    api_client, checkout_with_fixed_discount_for_more_then_total, sale
):
    # given
    checkout = checkout_with_fixed_discount_for_more_then_total
    variables = {"token": str(checkout.token)}

    # when
    response = api_client.post_graphql(CHECKOUT_DISCOUNTS_CALCULATIONS_QUERY, variables)
    content = get_graphql_content(response)

    # then
    checkout_data = content["data"]["checkout"]
    discount_data = checkout_data["discounts"][0]
    checkout_total = checkout_data["totalPrice"]["gross"]["amount"]
    checkout_subtotal = checkout_data["subtotalPrice"]["gross"]["amount"]
    checkout_shipping_price = checkout_data["shippingPrice"]["gross"]["amount"]
    checkout_undiscounted_total = checkout_subtotal + checkout_shipping_price

    assert checkout_total == 0
    assert discount_data["amount"]["amount"] + checkout_total == round(
        checkout_subtotal + checkout_shipping_price, 2
    )
    assert discount_data["amount"]["amount"] == checkout_undiscounted_total
    assert discount_data["value"] > checkout_total


def test_checkout_pricing_with_percentage_discount(
    api_client, checkout_with_percentage_discount, sale
):
    # given
    checkout = checkout_with_percentage_discount
    variables = {"token": str(checkout.token)}

    # when
    response = api_client.post_graphql(CHECKOUT_DISCOUNTS_CALCULATIONS_QUERY, variables)
    content = get_graphql_content(response)

    # then
    checkout_data = content["data"]["checkout"]
    discount_data = checkout_data["discounts"][0]
    checkout_total = checkout_data["totalPrice"]["gross"]["amount"]
    checkout_subtotal = checkout_data["subtotalPrice"]["gross"]["amount"]
    checkout_shipping_price = checkout_data["shippingPrice"]["gross"]["amount"]
    checkout_undiscounted_total = checkout_subtotal + checkout_shipping_price

    assert checkout_total > 0
    assert checkout_undiscounted_total > checkout_total
    assert discount_data["amount"]["amount"] + checkout_total == round(
        checkout_subtotal + checkout_shipping_price, 2
    )
    assert discount_data["value"] == 20
    assert discount_data["amount"]["amount"] == round(
        checkout_undiscounted_total * 0.2, 2
    )


def test_checkout_pricing_with_percentage_discount_for_whole_checkout(
    api_client, checkout_with_100_percentage_discount, sale
):
    # given
    checkout = checkout_with_100_percentage_discount
    variables = {"token": str(checkout.token)}

    # when
    response = api_client.post_graphql(CHECKOUT_DISCOUNTS_CALCULATIONS_QUERY, variables)
    content = get_graphql_content(response)

    # then
    checkout_data = content["data"]["checkout"]
    discount_data = checkout_data["discounts"][0]
    checkout_total = checkout_data["totalPrice"]["gross"]["amount"]
    checkout_subtotal = checkout_data["subtotalPrice"]["gross"]["amount"]
    checkout_shipping_price = checkout_data["shippingPrice"]["gross"]["amount"]
    checkout_undiscounted_total = checkout_subtotal + checkout_shipping_price

    assert checkout_total == 0
    assert discount_data["value"] == 100
    assert discount_data["amount"]["amount"] == checkout_undiscounted_total
