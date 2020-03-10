import pytest
from graphene import Node

from saleor.checkout import calculations
from saleor.checkout.models import Checkout
from tests.api.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_create_checkout_as_anonymous(
    api_client,
    graphql_address_data,
    stock,
    product_with_default_variant,
    product_with_single_variant,
    product_with_two_variants,
    count_queries,
):
    query = """
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

      fragment CheckoutLine on CheckoutLine {
        id
        quantity
        totalPrice {
          ...Price
        }
        variant {
          stockQuantity
          ...ProductVariant
        }
        quantity
      }

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

      fragment ShippingMethod on ShippingMethod {
        id
        name
        price {
          currency
          amount
        }
      }

      fragment Checkout on Checkout {
        availablePaymentGateways {
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

    checkout_counts = Checkout.objects.count()
    variables = {
        "checkoutInput": {
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
                        "ProductVariant", product_with_two_variants.variants.first().pk,
                    ),
                },
                {
                    "quantity": 2,
                    "variantId": Node.to_global_id(
                        "ProductVariant", product_with_two_variants.variants.last().pk,
                    ),
                },
            ],
        }
    }
    get_graphql_content(api_client.post_graphql(query, variables))
    assert checkout_counts + 1 == Checkout.objects.count()


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_add_shipping_to_checkout_as_anonymous(
    api_client, checkout_with_shipping_address, shipping_method, count_queries,
):
    query = """
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

        fragment CheckoutLine on CheckoutLine {
          id
          quantity
          totalPrice {
            ...Price
          }
          variant {
            stockQuantity
            ...ProductVariant
          }
        }

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
        }

        fragment ShippingMethod on ShippingMethod {
          id
          name
          price {
            currency
            amount
          }
        }

        fragment Checkout on Checkout {
          availablePaymentGateways {
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

        mutation updateCheckoutShippingOptions(
          $checkoutId: ID!, $shippingMethodId: ID!
        ) {
          checkoutShippingMethodUpdate(
            checkoutId: $checkoutId, shippingMethodId: $shippingMethodId
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
    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_shipping_address.pk),
        "shippingMethodId": Node.to_global_id("ShippingMethod", shipping_method.pk),
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutShippingMethodUpdate"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_add_billing_address_to_checkout_as_anonymous(
    api_client, graphql_address_data, checkout_with_shipping_method, count_queries
):
    query = """
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

        fragment CheckoutLine on CheckoutLine {
          id
          quantity
          totalPrice {
            ...Price
          }
          variant {
            stockQuantity
            ...ProductVariant
          }
          quantity
        }

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

        fragment ShippingMethod on ShippingMethod {
          id
          name
          price {
            currency
            amount
          }
        }

        fragment Checkout on Checkout {
          availablePaymentGateways {
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

        mutation UpdateCheckoutBillingAddress(
          $checkoutId: ID!, $billingAddress: AddressInput!
        ) {
          checkoutBillingAddressUpdate(
              checkoutId: $checkoutId, billingAddress: $billingAddress
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
    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_shipping_method.pk),
        "billingAddress": graphql_address_data,
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutBillingAddressUpdate"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_update_checkout_lines_as_anonymous(
    api_client,
    graphql_address_data,
    checkout_with_variant,
    stock,
    product_with_default_variant,
    product_with_single_variant,
    product_with_two_variants,
    count_queries,
):
    query = """
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

        fragment CheckoutLine on CheckoutLine {
          id
          quantity
          totalPrice {
            ...Price
          }
          variant {
            stockQuantity
            ...ProductVariant
          }
        }

        mutation updateCheckoutLine($checkoutId: ID!, $lines: [CheckoutLineInput]!) {
          checkoutLinesUpdate(checkoutId: $checkoutId, lines: $lines) {
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
    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_variant.pk),
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
                    "ProductVariant", product_with_default_variant.variants.first().pk,
                ),
            },
            {
                "quantity": 10,
                "variantId": Node.to_global_id(
                    "ProductVariant", product_with_single_variant.variants.first().pk,
                ),
            },
            {
                "quantity": 3,
                "variantId": Node.to_global_id(
                    "ProductVariant", product_with_two_variants.variants.first().pk,
                ),
            },
            {
                "quantity": 2,
                "variantId": Node.to_global_id(
                    "ProductVariant", product_with_two_variants.variants.last().pk,
                ),
            },
        ],
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutLinesUpdate"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_checkout_shipping_address_update_as_anonymous(
    api_client, graphql_address_data, checkout_with_variant, count_queries
):
    query = """
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

        fragment CheckoutLine on CheckoutLine {
          id
          quantity
          totalPrice {
            ...Price
          }
          variant {
            stockQuantity
            ...ProductVariant
          }
          quantity
        }

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

        fragment ShippingMethod on ShippingMethod {
          id
          name
          price {
            currency
            amount
          }
        }

        fragment Checkout on Checkout {
          availablePaymentGateways {
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

        mutation UpdateCheckoutShippingAddress(
          $checkoutId: ID!, $shippingAddress: AddressInput!, $email: String!
        ) {
          checkoutShippingAddressUpdate(
            checkoutId: $checkoutId, shippingAddress: $shippingAddress
          ) {
            errors {
              field
              message
            }
            checkout {
              ...Checkout
            }
          }
          checkoutEmailUpdate(checkoutId: $checkoutId, email: $email) {
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
    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_variant.pk),
        "email": "newEmail@example.com",
        "shippingAddress": graphql_address_data,
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutShippingAddressUpdate"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_checkout_voucher_code_as_anonymous(
    api_client, checkout_with_billing_address, voucher, count_queries
):
    query = """
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

        fragment CheckoutLine on CheckoutLine {
          id
          quantity
          totalPrice {
            ...Price
          }
          variant {
            stockQuantity
            ...ProductVariant
          }
          quantity
        }

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

        fragment ShippingMethod on ShippingMethod {
          id
          name
          price {
            currency
            amount
          }
        }

        fragment Checkout on Checkout {
          availablePaymentGateways {
            name
            config {
              field
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

        mutation AddCheckoutPromoCode($checkoutId: ID!, $promoCode: String!) {
          checkoutAddPromoCode(checkoutId: $checkoutId, promoCode: $promoCode) {
            checkout {
              ...Checkout
            }
            errors {
              field
              message
            }
            checkoutErrors {
              field
              message
              code
            }
          }
        }
    """
    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_billing_address.pk),
        "promoCode": voucher.code,
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutAddPromoCode"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_checkout_payment_charge_as_anonymous(
    api_client, checkout_with_billing_address, count_queries
):
    query = """
        mutation createPayment($input: PaymentInput!, $checkoutId: ID!) {
          checkoutPaymentCreate(input: $input, checkoutId: $checkoutId) {
            errors {
              field
              message
            }
          }
        }
    """

    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_billing_address.pk),
        "input": {
            "amount": calculations.checkout_total(
                checkout=checkout_with_billing_address
            ).gross.amount,
            "gateway": "Dummy",
            "token": "charged",
        },
    }
    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutPaymentCreate"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_complete_checkout(api_client, checkout_with_charged_payment, count_queries):
    query = """
        mutation completeCheckout($checkoutId: ID!) {
          checkoutComplete(checkoutId: $checkoutId) {
            errors {
              field
              message
            }
            order {
              id
              token
            }
          }
        }
    """

    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_charged_payment.pk),
    }

    response = get_graphql_content(api_client.post_graphql(query, variables))
    assert not response["data"]["checkoutComplete"]["errors"]
