import pytest
from graphene import Node

from .....checkout import calculations
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout
from .....plugins.manager import get_plugins_manager
from ....tests.utils import get_graphql_content

FRAGMENT_PRICE = """
    fragment Price on TaxedMoney {
      gross {
        amount
        currency
      }
      net {
        amount
        currency
      }
    }
"""

FRAGMENT_PRODUCT_VARIANT = (
    FRAGMENT_PRICE
    + """
        fragment ProductVariant on ProductVariant {
          id
          name
          pricing {
            onSale
            priceUndiscounted {
              ...Price
            }
            price {
              ...Price
            }
          }
          product {
            id
            name
            thumbnail {
              url
              alt
            }
            thumbnail2x: thumbnail(size: 510) {
              url
            }
          }
        }
    """
)

FRAGMENT_CHECKOUT_LINE = (
    FRAGMENT_PRODUCT_VARIANT
    + """
        fragment CheckoutLine on CheckoutLine {
          id
          quantity
          totalPrice {
            ...Price
          }
          variant {
            ...ProductVariant
          }
          quantity
        }
    """
)

FRAGMENT_ADDRESS = """
    fragment Address on Address {
      id
      firstName
      lastName
      companyName
      streetAddress1
      streetAddress2
      city
      postalCode
      country {
        code
        country
      }
      countryArea
      phone
      isDefaultBillingAddress
      isDefaultShippingAddress
    }
"""


FRAGMENT_SHIPPING_METHOD = """
    fragment ShippingMethod on ShippingMethod {
        id
        name
        price {
            amount
        }
    }
"""


FRAGMENT_CHECKOUT = (
    FRAGMENT_CHECKOUT_LINE
    + FRAGMENT_ADDRESS
    + FRAGMENT_SHIPPING_METHOD
    + """
        fragment Checkout on Checkout {
          availablePaymentGateways {
            id
            name
            config {
              field
              value
            }
          }
          token
          id
          totalPrice {
            ...Price
          }
          subtotalPrice {
            ...Price
          }
          billingAddress {
            ...Address
          }
          shippingAddress {
            ...Address
          }
          email
          availableShippingMethods {
            ...ShippingMethod
          }
          shippingMethod {
            ...ShippingMethod
          }
          shippingPrice {
            ...Price
          }
          lines {
            ...CheckoutLine
          }
          isShippingRequired
          discount {
            currency
            amount
          }
          discountName
          translatedDiscountName
          voucherCode
        }
    """
)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_create_checkout(
    api_client,
    graphql_address_data,
    stock,
    channel_USD,
    product_with_default_variant,
    product_with_single_variant,
    product_with_two_variants,
    count_queries,
):
    query = (
        FRAGMENT_CHECKOUT
        + """
            mutation CreateCheckout($checkoutInput: CheckoutCreateInput!) {
              checkoutCreate(input: $checkoutInput) {
                errors {
                  field
                  message
                }
                checkout {
                  ...Checkout
                }
              }
            }
        """
    )
    checkout_counts = Checkout.objects.count()
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "email": "test@example.com",
            "shippingAddress": graphql_address_data,
            "lines": [
                {
                    "quantity": 1,
                    "variantId": Node.to_global_id(
                        "ProductVariant", stock.product_variant.pk
                    ),
                },
                {
                    "quantity": 2,
                    "variantId": Node.to_global_id(
                        "ProductVariant",
                        product_with_default_variant.variants.first().pk,
                    ),
                },
                {
                    "quantity": 10,
                    "variantId": Node.to_global_id(
                        "ProductVariant",
                        product_with_single_variant.variants.first().pk,
                    ),
                },
                {
                    "quantity": 3,
                    "variantId": Node.to_global_id(
                        "ProductVariant",
                        product_with_two_variants.variants.first().pk,
                    ),
                },
                {
                    "quantity": 2,
                    "variantId": Node.to_global_id(
                        "ProductVariant",
                        product_with_two_variants.variants.last().pk,
                    ),
                },
            ],
        }
    }
    get_graphql_content(api_client.post_graphql(query, variables))
    assert checkout_counts + 1 == Checkout.objects.count()


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_add_shipping_to_checkout(
    api_client,
    checkout_with_shipping_address,
    shipping_method,
    count_queries,
):
    query = (
        FRAGMENT_CHECKOUT
        + """
            mutation updateCheckoutShippingOptions(
              $token: UUID, $shippingMethodId: ID!
            ) {
              checkoutShippingMethodUpdate(
                token: $token, shippingMethodId: $shippingMethodId
              ) {
                errors {
                  field
                  message
                }
                checkout {
                  ...Checkout
                }
              }
            }
        """
    )
    variables = {
        "token": checkout_with_shipping_address.token,
        "shippingMethodId": Node.to_global_id("ShippingMethod", shipping_method.pk),
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutShippingMethodUpdate"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_add_billing_address_to_checkout(
    api_client, graphql_address_data, checkout_with_shipping_method, count_queries
):
    query = (
        FRAGMENT_CHECKOUT
        + """
            mutation UpdateCheckoutBillingAddress(
              $token: UUID, $billingAddress: AddressInput!
            ) {
              checkoutBillingAddressUpdate(
                  token: $token, billingAddress: $billingAddress
              ) {
                errors {
                  field
                  message
                }
                checkout {
                  ...Checkout
                }
              }
            }
        """
    )
    variables = {
        "token": checkout_with_shipping_method.token,
        "billingAddress": graphql_address_data,
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutBillingAddressUpdate"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_update_checkout_lines(
    api_client,
    checkout_with_items,
    stock,
    product_with_default_variant,
    product_with_single_variant,
    product_with_two_variants,
    count_queries,
):
    query = (
        FRAGMENT_CHECKOUT_LINE
        + """
            mutation updateCheckoutLine($token: UUID, $lines: [CheckoutLineInput]!){
              checkoutLinesUpdate(token: $token, lines: $lines) {
                checkout {
                  id
                  lines {
                    ...CheckoutLine
                  }
                  totalPrice {
                    ...Price
                  }
                  subtotalPrice {
                    ...Price
                  }
                  isShippingRequired
                }
                errors {
                  field
                  message
                }
              }
            }
        """
    )
    variables = {
        "token": checkout_with_items.token,
        "lines": [
            {
                "quantity": 1,
                "variantId": Node.to_global_id(
                    "ProductVariant", stock.product_variant.pk
                ),
            },
            {
                "quantity": 2,
                "variantId": Node.to_global_id(
                    "ProductVariant",
                    product_with_default_variant.variants.first().pk,
                ),
            },
            {
                "quantity": 10,
                "variantId": Node.to_global_id(
                    "ProductVariant",
                    product_with_single_variant.variants.first().pk,
                ),
            },
            {
                "quantity": 3,
                "variantId": Node.to_global_id(
                    "ProductVariant",
                    product_with_two_variants.variants.first().pk,
                ),
            },
            {
                "quantity": 2,
                "variantId": Node.to_global_id(
                    "ProductVariant",
                    product_with_two_variants.variants.last().pk,
                ),
            },
        ],
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutLinesUpdate"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_add_checkout_lines(
    api_client,
    checkout_with_single_item,
    stock,
    product_with_default_variant,
    product_with_single_variant,
    product_with_two_variants,
    count_queries,
):
    query = (
        FRAGMENT_CHECKOUT_LINE
        + """
            mutation addCheckoutLines($checkoutId: ID!, $lines: [CheckoutLineInput]!){
              checkoutLinesAdd(checkoutId: $checkoutId, lines: $lines) {
                checkout {
                  id
                  lines {
                    ...CheckoutLine
                  }
                }
                errors {
                  field
                  message
                }
              }
            }
        """
    )
    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_single_item.pk),
        "lines": [
            {
                "quantity": 1,
                "variantId": Node.to_global_id(
                    "ProductVariant", stock.product_variant.pk
                ),
            },
            {
                "quantity": 2,
                "variantId": Node.to_global_id(
                    "ProductVariant",
                    product_with_default_variant.variants.first().pk,
                ),
            },
            {
                "quantity": 10,
                "variantId": Node.to_global_id(
                    "ProductVariant",
                    product_with_single_variant.variants.first().pk,
                ),
            },
            {
                "quantity": 3,
                "variantId": Node.to_global_id(
                    "ProductVariant",
                    product_with_two_variants.variants.first().pk,
                ),
            },
            {
                "quantity": 2,
                "variantId": Node.to_global_id(
                    "ProductVariant",
                    product_with_two_variants.variants.last().pk,
                ),
            },
        ],
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutLinesAdd"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_checkout_shipping_address_update(
    api_client, graphql_address_data, checkout_with_variants, count_queries
):
    query = (
        FRAGMENT_CHECKOUT
        + """
            mutation UpdateCheckoutShippingAddress(
              $token: UUID, $shippingAddress: AddressInput!
            ) {
              checkoutShippingAddressUpdate(
                token: $token, shippingAddress: $shippingAddress
              ) {
                errors {
                  field
                  message
                }
                checkout {
                  ...Checkout
                }
              }
            }
        """
    )
    variables = {
        "token": checkout_with_variants.pk,
        "shippingAddress": graphql_address_data,
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutShippingAddressUpdate"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_checkout_email_update(api_client, checkout_with_variants, count_queries):
    query = (
        FRAGMENT_CHECKOUT
        + """
            mutation UpdateCheckoutEmail(
              $token: UUID, $email: String!
            ) {
              checkoutEmailUpdate(token: $token, email: $email) {
                checkout {
                  ...Checkout
                }
                errors {
                  field
                  message
                }
              }
            }
        """
    )
    variables = {
        "token": checkout_with_variants.token,
        "email": "newEmail@example.com",
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutEmailUpdate"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_checkout_voucher_code(
    api_client, checkout_with_billing_address, voucher, count_queries
):
    query = (
        FRAGMENT_CHECKOUT
        + """
            mutation AddCheckoutPromoCode($token: UUID, $promoCode: String!) {
              checkoutAddPromoCode(token: $token, promoCode: $promoCode) {
                checkout {
                  ...Checkout
                }
                errors {
                  field
                  message
                }
                errors {
                  field
                  message
                  code
                }
              }
            }
        """
    )
    variables = {
        "token": checkout_with_billing_address.token,
        "promoCode": voucher.code,
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutAddPromoCode"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_checkout_payment_charge(
    api_client, checkout_with_billing_address, count_queries
):
    query = """
        mutation createPayment($input: PaymentInput!, $token: UUID) {
          checkoutPaymentCreate(input: $input, token: $token) {
            errors {
              field
              message
            }
          }
        }
    """

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout_with_billing_address)
    checkout_info = fetch_checkout_info(
        checkout_with_billing_address, lines, [], manager
    )
    manager = get_plugins_manager()
    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_billing_address.shipping_address,
    )

    variables = {
        "token": checkout_with_billing_address.token,
        "input": {
            "amount": total.gross.amount,
            "gateway": "mirumee.payments.dummy",
            "token": "charged",
        },
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutPaymentCreate"]["errors"]


ORDER_PRICE_FRAGMENT = """
fragment OrderPrice on TaxedMoney {
  gross {
    amount
    currency
    __typename
  }
  net {
    amount
    currency
    __typename
  }
  __typename
}
"""


FRAGMENT_ORDER_DETAIL = (
    FRAGMENT_ADDRESS
    + FRAGMENT_PRODUCT_VARIANT
    + ORDER_PRICE_FRAGMENT
    + """
  fragment OrderDetail on Order {
    userEmail
    paymentStatus
    paymentStatusDisplay
    status
    statusDisplay
    id
    token
    number
    shippingAddress {
      ...Address
      __typename
    }
    lines {
      productName
      quantity
      variant {
        ...ProductVariant
        __typename
      }
      unitPrice {
        currency
        ...OrderPrice
        __typename
      }
      totalPrice {
        currency
        ...OrderPrice
        __typename
      }
      __typename
    }
    subtotal {
      ...OrderPrice
      __typename
    }
    total {
      ...OrderPrice
      __typename
    }
    shippingPrice {
      ...OrderPrice
      __typename
    }
    __typename
  }
  """
)


COMPLETE_CHECKOUT_MUTATION = (
    FRAGMENT_ORDER_DETAIL
    + """
    mutation completeCheckout($token: UUID) {
      checkoutComplete(token: $token) {
        errors {
          code
          field
          message
        }
        order {
          ...OrderDetail
          __typename
        }
        confirmationNeeded
        confirmationData
      }
    }
"""
)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_complete_checkout(api_client, checkout_with_charged_payment, count_queries):
    query = COMPLETE_CHECKOUT_MUTATION

    variables = {
        "token": checkout_with_charged_payment.token,
    }

    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutComplete"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_complete_checkout_with_single_line(
    api_client, checkout_with_charged_payment, count_queries
):
    query = COMPLETE_CHECKOUT_MUTATION
    checkout_with_charged_payment.lines.set(
        [checkout_with_charged_payment.lines.first()]
    )

    variables = {
        "token": checkout_with_charged_payment.token,
    }

    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutComplete"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_customer_complete_checkout(
    api_client, checkout_with_charged_payment, count_queries, customer_user
):
    query = COMPLETE_CHECKOUT_MUTATION
    checkout = checkout_with_charged_payment
    checkout.user = customer_user
    checkout.save()
    variables = {
        "token": checkout.token,
    }

    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutComplete"]["errors"]
