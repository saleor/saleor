import pytest
from django.conf import settings
from graphene import Node

from saleor.checkout.utils import add_variant_to_checkout
from saleor.payment import ChargeStatus, TransactionKind
from saleor.payment.models import Payment
from tests.api.utils import get_graphql_content


@pytest.fixture()
def checkout_with_variant(checkout, variant):
    add_variant_to_checkout(checkout, variant, 1)
    checkout.save()
    return checkout


@pytest.fixture()
def checkout_with_shipping_method(checkout_with_variant, shipping_method):
    checkout = checkout_with_variant

    checkout.shipping_method = shipping_method
    checkout.save()

    return checkout


@pytest.fixture()
def checkout_with_billing_address(checkout_with_shipping_method, address):
    checkout = checkout_with_shipping_method

    checkout.billing_address = address
    checkout.save()

    return checkout


@pytest.fixture()
def checkout_with_charged_payment(checkout_with_billing_address):
    checkout = checkout_with_billing_address

    payment = Payment.objects.create(
        gateway=settings.DUMMY,
        is_active=True,
        total=checkout.get_total().gross.amount,
        currency="USD",
    )

    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.checkout = checkout_with_billing_address
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )

    return checkout


@pytest.mark.django_db
@pytest.mark.count_queries
def test_create_checkout(api_client, graphql_address_data, variant):
    query = """
        fragment Price on TaxedMoney {
          gross {
            amount
            localized
            __typename
          }
          currency
          __typename
        }

        fragment ProductVariant on ProductVariant {
          id
          name
          price {
            amount
            currency
            localized
            __typename
          }
          product {
            id
            name
            thumbnail {
              url
              alt
              __typename
            }
            thumbnail2x: thumbnail(size: 510) {
              url
              __typename
            }
            __typename
          }
          __typename
        }

        fragment CheckoutLine on CheckoutLine {
          id
          quantity
          totalPrice {
            ...Price
            __typename
          }
          variant {
            stockQuantity
            ...ProductVariant
            __typename
          }
          quantity
          __typename
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
            __typename
          }
          countryArea
          phone
          __typename
        }

        fragment ShippingMethod on ShippingMethod {
          id
          name
          price {
            currency
            amount
            localized
            __typename
          }
          __typename
        }

        fragment Checkout on Checkout {
          availablePaymentGateways
          token
          id
          user {
            email
            __typename
          }
          totalPrice {
            ...Price
            __typename
          }
          subtotalPrice {
            ...Price
            __typename
          }
          billingAddress {
            ...Address
            __typename
          }
          shippingAddress {
            ...Address
            __typename
          }
          email
          availableShippingMethods {
            ...ShippingMethod
            __typename
          }
          shippingMethod {
            ...ShippingMethod
            __typename
          }
          shippingPrice {
            ...Price
            __typename
          }
          lines {
            ...CheckoutLine
            __typename
          }
          __typename
        }

        mutation createCheckout($checkoutInput: CheckoutCreateInput!) {
          checkoutCreate(input: $checkoutInput) {
            errors {
              field
              message
              __typename
            }
            checkout {
              ...Checkout
              __typename
            }
            __typename
          }
        }
    """
    variables = {
        "checkoutInput": {
            "email": "test@example.com",
            "shippingAddress": graphql_address_data,
            "lines": [
                {
                    "quantity": 1,
                    "variantId": Node.to_global_id("ProductVariant", variant.pk),
                }
            ],
        }
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries
def test_add_shipping_to_checkout(
    api_client, graphql_address_data, variant, checkout_with_variant, shipping_method
):
    query = """
        fragment Price on TaxedMoney {
          gross {
            amount
            localized
            __typename
          }
          currency
          __typename
        }

        fragment ProductVariant on ProductVariant {
          id
          name
          price {
            amount
            currency
            localized
            __typename
          }
          product {
            id
            name
            thumbnail {
              url
              alt
              __typename
            }
            thumbnail2x: thumbnail(size: 510) {
              url
              __typename
            }
            __typename
          }
          __typename
        }

        fragment CheckoutLine on CheckoutLine {
          id
          quantity
          totalPrice {
            ...Price
            __typename
          }
          variant {
            stockQuantity
            ...ProductVariant
            __typename
          }
          quantity
          __typename
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
            __typename
          }
          countryArea
          phone
          __typename
        }

        fragment ShippingMethod on ShippingMethod {
          id
          name
          price {
            currency
            amount
            localized
            __typename
          }
          __typename
        }

        fragment Checkout on Checkout {
          availablePaymentGateways
          token
          id
          user {
            email
            __typename
          }
          totalPrice {
            ...Price
            __typename
          }
          subtotalPrice {
            ...Price
            __typename
          }
          billingAddress {
            ...Address
            __typename
          }
          shippingAddress {
            ...Address
            __typename
          }
          email
          availableShippingMethods {
            ...ShippingMethod
            __typename
          }
          shippingMethod {
            ...ShippingMethod
            __typename
          }
          shippingPrice {
            ...Price
            __typename
          }
          lines {
            ...CheckoutLine
            __typename
          }
          __typename
        }

        mutation updateCheckoutShippingOptions(
          $checkoutId: ID!
          $shippingMethodId: ID!
        ) {
          checkoutShippingMethodUpdate(
            checkoutId: $checkoutId
            shippingMethodId: $shippingMethodId
          ) {
            errors {
              field
              message
              __typename
            }
            checkout {
              ...Checkout
              __typename
            }
            __typename
          }
        }
    """
    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_variant.pk),
        "shippingMethodId": Node.to_global_id("ShippingMethod", shipping_method.pk),
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries
def test_add_billing_address_to_checkout(
    api_client, graphql_address_data, checkout_with_shipping_method
):
    query = """
        fragment Price on TaxedMoney {
          gross {
            amount
            localized
            __typename
          }
          currency
          __typename
        }

        fragment ProductVariant on ProductVariant {
          id
          name
          price {
            amount
            currency
            localized
            __typename
          }
          product {
            id
            name
            thumbnail {
              url
              alt
              __typename
            }
            thumbnail2x: thumbnail(size: 510) {
              url
              __typename
            }
            __typename
          }
          __typename
        }

        fragment CheckoutLine on CheckoutLine {
          id
          quantity
          totalPrice {
            ...Price
            __typename
          }
          variant {
            stockQuantity
            ...ProductVariant
            __typename
          }
          quantity
          __typename
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
            __typename
          }
          countryArea
          phone
          __typename
        }

        fragment ShippingMethod on ShippingMethod {
          id
          name
          price {
            currency
            amount
            localized
            __typename
          }
          __typename
        }

        fragment Checkout on Checkout {
          availablePaymentGateways
          token
          id
          user {
            email
            __typename
          }
          totalPrice {
            ...Price
            __typename
          }
          subtotalPrice {
            ...Price
            __typename
          }
          billingAddress {
            ...Address
            __typename
          }
          shippingAddress {
            ...Address
            __typename
          }
          email
          availableShippingMethods {
            ...ShippingMethod
            __typename
          }
          shippingMethod {
            ...ShippingMethod
            __typename
          }
          shippingPrice {
            ...Price
            __typename
          }
          lines {
            ...CheckoutLine
            __typename
          }
          __typename
        }

        mutation updateCheckoutBillingAddress(
          $checkoutId: ID!
          $billingAddress: AddressInput!
        ) {
          checkoutBillingAddressUpdate(
            checkoutId: $checkoutId
            billingAddress: $billingAddress
          ) {
            errors {
              field
              message
              __typename
            }
            checkout {
              ...Checkout
              __typename
            }
            __typename
          }
        }
    """
    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_shipping_method.pk),
        "billingAddress": graphql_address_data,
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries
def test_checkout_payment_charge(
    api_client, graphql_address_data, checkout_with_billing_address
):
    query = """
        mutation createPayment($input: PaymentInput!, $checkoutId: ID!) {
          checkoutPaymentCreate(input: $input, checkoutId: $checkoutId) {
            errors {
              field
              message
              __typename
            }
            __typename
          }
        }
    """

    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_billing_address.pk),
        "input": {
            "billingAddress": graphql_address_data,
            "amount": 1000,  # 10.00 USD * 100
            "gateway": settings.DUMMY.upper(),
            "token": "charged",
        },
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries
def test_complete_checkout(api_client, checkout_with_charged_payment):
    query = """
        mutation completeCheckout($checkoutId: ID!) {
          checkoutComplete(checkoutId: $checkoutId) {
            errors {
              field
              message
              __typename
            }
            order {
              id
              token
              __typename
            }
            __typename
          }
        }
    """

    variables = {
        "checkoutId": Node.to_global_id("Checkout", checkout_with_charged_payment.pk)
    }

    get_graphql_content(api_client.post_graphql(query, variables))
