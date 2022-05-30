from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest
from graphene import Node

from .....checkout import calculations
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout
from .....checkout.utils import add_variants_to_checkout, set_external_shipping_id
from .....plugins.manager import get_plugins_manager
from .....product.models import ProductVariant, ProductVariantChannelListing
from .....warehouse.models import Stock
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content
from ...mutations.utils import CheckoutLineData

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

FRAGMENT_COLLECTION_POINT = """
   fragment CollectionPoint on Warehouse {
        id
        name
        isPrivate
        clickAndCollectOption
        address {
             streetAddress1
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
          stockReservationExpires
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

FRAGMENT_CHECKOUT_FOR_CC = (
    FRAGMENT_CHECKOUT_LINE
    + FRAGMENT_ADDRESS
    + FRAGMENT_SHIPPING_METHOD
    + FRAGMENT_COLLECTION_POINT
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
          availableCollectionPoints {
            ...CollectionPoint
          }
          deliveryMethod {
            __typename
            ... on ShippingMethod {
              ...ShippingMethod
            }
            ... on Warehouse {
              ...CollectionPoint
            }
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


MUTATION_CHECKOUT_CREATE = (
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
    get_graphql_content(api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables))
    assert checkout_counts + 1 == Checkout.objects.count()


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_create_checkout_for_cc(
    api_client,
    graphql_address_data,
    channel_USD,
    stocks_for_cc,
    product_variant_list,
    count_queries,
):
    query = (
        FRAGMENT_CHECKOUT_FOR_CC
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
                        "ProductVariant", stocks_for_cc[0].product_variant.pk
                    ),
                },
                {
                    "quantity": 2,
                    "variantId": Node.to_global_id(
                        "ProductVariant",
                        product_variant_list[0].pk,
                    ),
                },
                {
                    "quantity": 5,
                    "variantId": Node.to_global_id(
                        "ProductVariant",
                        product_variant_list[1].pk,
                    ),
                },
            ],
        }
    }
    get_graphql_content(api_client.post_graphql(query, variables))
    assert checkout_counts + 1 == Checkout.objects.count()


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_create_checkout_with_reservations(
    site_settings_with_reservations,
    api_client,
    product,
    stock,
    warehouse,
    graphql_address_data,
    channel_USD,
    django_assert_num_queries,
    count_queries,
):
    # TODO: replace this with MUTATION_CHECKOUT_CREATE when query number stabilizes
    query = (
        FRAGMENT_CHECKOUT_LINE
        + """
            mutation CreateCheckout($checkoutInput: CheckoutCreateInput!) {
              checkoutCreate(input: $checkoutInput) {
                errors {
                  field
                  message
                }
                checkout {
                  lines {
                    ...CheckoutLine
                  }
                  stockReservationExpires
                }
              }
            }
        """
    )

    variants = ProductVariant.objects.bulk_create(
        [ProductVariant(product=product, sku=f"SKU_A_{i}") for i in range(10)]
    )
    ProductVariantChannelListing.objects.bulk_create(
        [
            ProductVariantChannelListing(
                variant=variant,
                channel=channel_USD,
                price_amount=Decimal(10),
                cost_price_amount=Decimal(1),
                currency=channel_USD.currency_code,
            )
            for variant in variants
        ]
    )
    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=15)
            for variant in variants
        ]
    )

    new_lines = []
    for variant in variants:
        variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
        new_lines.append({"quantity": 2, "variantId": variant_id})

    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [new_lines[0]],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    with django_assert_num_queries(53):
        response = api_client.post_graphql(query, variables)
        assert get_graphql_content(response)["data"]["checkoutCreate"]
        assert Checkout.objects.first().lines.count() == 1

    Checkout.objects.all().delete()

    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": new_lines,
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    with django_assert_num_queries(53):
        response = api_client.post_graphql(query, variables)
        assert get_graphql_content(response)["data"]["checkoutCreate"]
        assert Checkout.objects.first().lines.count() == 10


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
              $id: ID, $shippingMethodId: ID!
            ) {
              checkoutShippingMethodUpdate(
                id: $id, shippingMethodId: $shippingMethodId
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
        "id": to_global_id_or_none(checkout_with_shipping_address),
        "shippingMethodId": Node.to_global_id("ShippingMethod", shipping_method.pk),
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutShippingMethodUpdate"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_add_delivery_to_checkout(
    api_client,
    checkout_with_shipping_address_for_cc,
    warehouses_for_cc,
    count_queries,
):
    query = (
        FRAGMENT_CHECKOUT
        + """
            mutation updateCheckoutDeliveryOptions(
              $id: ID, $deliveryMethodId: ID
            ) {
              checkoutDeliveryMethodUpdate(
                id: $id, deliveryMethodId: $deliveryMethodId
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
        "id": to_global_id_or_none(checkout_with_shipping_address_for_cc),
        "deliveryMethodId": Node.to_global_id("Warehouse", warehouses_for_cc[1].pk),
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutDeliveryMethodUpdate"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_add_billing_address_to_checkout(
    api_client, graphql_address_data, checkout_with_shipping_method, count_queries
):
    query = (
        FRAGMENT_CHECKOUT
        + """
            mutation UpdateCheckoutBillingAddress(
              $id: ID, $billingAddress: AddressInput!
            ) {
              checkoutBillingAddressUpdate(
                  id: $id, billingAddress: $billingAddress
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
        "id": to_global_id_or_none(checkout_with_shipping_method),
        "billingAddress": graphql_address_data,
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutBillingAddressUpdate"]["errors"]


MUTATION_CHECKOUT_LINES_UPDATE = (
    FRAGMENT_CHECKOUT_LINE
    + """
        mutation updateCheckoutLine($id: ID, $lines: [CheckoutLineUpdateInput!]!){
          checkoutLinesUpdate(id: $id, lines: $lines) {
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
    variables = {
        "id": to_global_id_or_none(checkout_with_items),
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
    response = get_graphql_content(
        api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    )
    assert not response["data"]["checkoutLinesUpdate"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_update_checkout_lines_with_reservations(
    site_settings_with_reservations,
    user_api_client,
    channel_USD,
    checkout_with_item,
    product,
    stock,
    warehouse,
    django_assert_num_queries,
    count_queries,
):
    checkout = checkout_with_item

    variants = ProductVariant.objects.bulk_create(
        [ProductVariant(product=product, sku=f"SKU_A_{i}") for i in range(10)]
    )
    ProductVariantChannelListing.objects.bulk_create(
        [
            ProductVariantChannelListing(
                variant=variant,
                channel=channel_USD,
                price_amount=Decimal(10),
                cost_price_amount=Decimal(1),
                currency=channel_USD.currency_code,
            )
            for variant in variants
        ]
    )
    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=15)
            for variant in variants
        ]
    )

    add_variants_to_checkout(
        checkout,
        variants,
        [
            CheckoutLineData(
                quantity=2,
                quantity_to_update=True,
                custom_price=None,
                custom_price_to_update=False,
            )
        ]
        * 10,
        channel_USD.slug,
        replace_reservations=True,
        reservation_length=5,
    )

    with django_assert_num_queries(56):
        variant_id = graphene.Node.to_global_id("ProductVariant", variants[0].pk)
        variables = {
            "id": to_global_id_or_none(checkout),
            "lines": [{"quantity": 3, "variantId": variant_id}],
        }
        response = user_api_client.post_graphql(
            MUTATION_CHECKOUT_LINES_UPDATE, variables
        )
        content = get_graphql_content(response)
        data = content["data"]["checkoutLinesUpdate"]
        assert not data["errors"]

    # Updating multiple lines in checkout has same query count as updating one
    with django_assert_num_queries(56):
        variables = {
            "id": to_global_id_or_none(checkout),
            "lines": [],
        }

        for variant in variants:
            variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
            variables["lines"].append({"quantity": 4, "variantId": variant_id})

        response = user_api_client.post_graphql(
            MUTATION_CHECKOUT_LINES_UPDATE, variables
        )
        content = get_graphql_content(response)
        data = content["data"]["checkoutLinesUpdate"]
        assert not data["errors"]


MUTATION_CHECKOUT_LINES_ADD = (
    FRAGMENT_CHECKOUT_LINE
    + """
        mutation addCheckoutLines($id: ID, $lines: [CheckoutLineInput!]!){
          checkoutLinesAdd(id: $id, lines: $lines) {
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


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
@patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_add_checkout_lines(
    mock_send_request,
    api_client,
    checkout_with_single_item,
    stock,
    product_with_default_variant,
    product_with_single_variant,
    product_with_two_variants,
    count_queries,
    shipping_app,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    mock_json_response = [
        {
            "id": "abcd",
            "name": "Provider - Economy",
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    mock_send_request.return_value = mock_json_response

    variables = {
        "id": Node.to_global_id("Checkout", checkout_with_single_item.pk),
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
    response = get_graphql_content(
        api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    )
    assert not response["data"]["checkoutLinesAdd"]["errors"]
    assert mock_send_request.call_count == 0


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
@patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_add_checkout_lines_with_external_shipping(
    mock_send_request,
    api_client,
    checkout_with_single_item,
    address,
    stock,
    product_with_default_variant,
    product_with_single_variant,
    product_with_two_variants,
    count_queries,
    shipping_app,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "abcd"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": "Provider - Economy",
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    mock_send_request.return_value = mock_json_response

    external_shipping_method_id = Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    checkout_with_single_item.shipping_address = address
    set_external_shipping_id(checkout_with_single_item, external_shipping_method_id)
    checkout_with_single_item.save()

    variables = {
        "id": Node.to_global_id("Checkout", checkout_with_single_item.pk),
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
    response = get_graphql_content(
        api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
    )
    assert not response["data"]["checkoutLinesAdd"]["errors"]
    # One api call:
    # - post-mutate() logic used to validate currently selected method
    assert mock_send_request.call_count == 1


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_add_checkout_lines_with_reservations(
    site_settings_with_reservations,
    user_api_client,
    channel_USD,
    checkout_with_item,
    product,
    stock,
    warehouse,
    django_assert_num_queries,
    count_queries,
):
    checkout = checkout_with_item
    line = checkout.lines.first()

    variants = ProductVariant.objects.bulk_create(
        [ProductVariant(product=product, sku=f"SKU_A_{i}") for i in range(10)]
    )
    ProductVariantChannelListing.objects.bulk_create(
        [
            ProductVariantChannelListing(
                variant=variant,
                channel=channel_USD,
                price_amount=Decimal(10),
                cost_price_amount=Decimal(1),
                currency=channel_USD.currency_code,
            )
            for variant in variants
        ]
    )
    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=15)
            for variant in variants
        ]
    )

    new_lines = []
    for variant in variants:
        variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
        new_lines.append({"quantity": 2, "variantId": variant_id})

    # Adding multiple lines to checkout has same query count as adding one
    with django_assert_num_queries(55):
        variables = {
            "id": Node.to_global_id("Checkout", checkout.pk),
            "lines": [new_lines[0]],
            "channelSlug": checkout.channel.slug,
        }
        response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
        content = get_graphql_content(response)
        data = content["data"]["checkoutLinesAdd"]
        assert not data["errors"]

    checkout.lines.exclude(id=line.id).delete()

    with django_assert_num_queries(55):
        variables = {
            "id": Node.to_global_id("Checkout", checkout.pk),
            "lines": new_lines,
            "channelSlug": checkout.channel.slug,
        }
        response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_ADD, variables)
        content = get_graphql_content(response)
        data = content["data"]["checkoutLinesAdd"]
        assert not data["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_checkout_shipping_address_update(
    api_client, graphql_address_data, checkout_with_variants, count_queries
):
    query = (
        FRAGMENT_CHECKOUT
        + """
            mutation UpdateCheckoutShippingAddress(
              $id: ID, $shippingAddress: AddressInput!
            ) {
              checkoutShippingAddressUpdate(
                id: $id, shippingAddress: $shippingAddress
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
        "id": to_global_id_or_none(checkout_with_variants),
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
              $id: ID, $email: String!
            ) {
              checkoutEmailUpdate(id: $id, email: $email) {
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
        "id": to_global_id_or_none(checkout_with_variants),
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
            mutation AddCheckoutPromoCode($id: ID, $promoCode: String!) {
              checkoutAddPromoCode(id: $id, promoCode: $promoCode) {
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
        "id": to_global_id_or_none(checkout_with_billing_address),
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
        mutation createPayment($input: PaymentInput!, $id: ID) {
          checkoutPaymentCreate(input: $input, id: $id) {
            errors {
              field
              message
            }
          }
        }
    """

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_billing_address)
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
        "id": to_global_id_or_none(checkout_with_billing_address),
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

FRAGMENT_ORDER_DETAIL_FOR_CC = (
    FRAGMENT_ADDRESS
    + FRAGMENT_PRODUCT_VARIANT
    + ORDER_PRICE_FRAGMENT
    + FRAGMENT_COLLECTION_POINT
    + FRAGMENT_SHIPPING_METHOD
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
    deliveryMethod {
      __typename
      ... on ShippingMethod {
        ...ShippingMethod
      }
      ... on Warehouse {
        ...CollectionPoint
      }
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

COMPLETE_CHECKOUT_MUTATION_PART = """
    mutation completeCheckout($id: ID) {
      checkoutComplete(id: $id) {
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


COMPLETE_CHECKOUT_MUTATION = FRAGMENT_ORDER_DETAIL + COMPLETE_CHECKOUT_MUTATION_PART

COMPLETE_CHECKOUT_MUTATION_FOR_CC = (
    FRAGMENT_ORDER_DETAIL_FOR_CC + COMPLETE_CHECKOUT_MUTATION_PART
)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_complete_checkout(api_client, checkout_with_charged_payment, count_queries):
    query = COMPLETE_CHECKOUT_MUTATION

    variables = {
        "id": to_global_id_or_none(checkout_with_charged_payment),
    }

    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutComplete"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_complete_checkout_with_out_of_stock_webhook(
    product_variant_out_of_stock_webhook_mock,
    api_client,
    checkout_with_charged_payment,
    count_queries,
):
    query = COMPLETE_CHECKOUT_MUTATION
    Stock.objects.update(quantity=10)
    variables = {
        "id": to_global_id_or_none(checkout_with_charged_payment),
    }

    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutComplete"]["errors"]
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.last()
    )


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
        "id": to_global_id_or_none(checkout_with_charged_payment),
    }

    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutComplete"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_complete_checkout_with_digital_line(
    api_client, checkout_with_digital_line_with_charged_payment, count_queries
):
    query = COMPLETE_CHECKOUT_MUTATION

    variables = {
        "id": to_global_id_or_none(checkout_with_digital_line_with_charged_payment),
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
        "id": to_global_id_or_none(checkout),
    }

    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutComplete"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_customer_complete_checkout_for_cc(
    api_client, checkout_with_charged_payment_for_cc, count_queries, customer_user
):
    query = COMPLETE_CHECKOUT_MUTATION_FOR_CC
    checkout = checkout_with_charged_payment_for_cc
    checkout.user = customer_user
    checkout.save()
    variables = {
        "id": to_global_id_or_none(checkout),
    }

    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutComplete"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_complete_checkout_preorder(
    api_client, checkout_preorder_with_charged_payment, count_queries
):
    query = COMPLETE_CHECKOUT_MUTATION

    variables = {
        "id": to_global_id_or_none(checkout_preorder_with_charged_payment),
    }

    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutComplete"]["errors"]
