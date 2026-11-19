import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from .....checkout.models import Checkout
from ....core.enums import LanguageCodeEnum
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content


def build_mutation(name, arguments):
    arguments = {"id": "ID", **arguments}
    definitions = ", ".join(f"${arg}: {type_}" for arg, type_ in arguments.items())
    passed = ", ".join(f"{arg}: ${arg}" for arg in arguments)
    return f"""
    mutation ({definitions}) {{
      {name}({passed}) {{
        errors {{ field message }}
      }}
    }}
    """


def lines_update(request, checkout):
    line = checkout.lines.get()
    return {"lines": [{"lineId": to_global_id_or_none(line), "quantity": 2}]}


def lines_add(request, checkout):
    variant = checkout.lines.get().variant
    return {
        "lines": [
            {
                "variantId": graphene.Node.to_global_id("ProductVariant", variant.pk),
                "quantity": 1,
            }
        ]
    }


def lines_delete(request, checkout):
    return {"linesIds": [to_global_id_or_none(checkout.lines.get())]}


def line_delete(request, checkout):
    return {"lineId": to_global_id_or_none(checkout.lines.get())}


def shipping_address(request, checkout):
    return {"shippingAddress": request.getfixturevalue("graphql_address_data")}


def billing_address(request, checkout):
    return {"billingAddress": request.getfixturevalue("graphql_address_data")}


def _with_shipping_address(request, checkout):
    checkout.shipping_address = request.getfixturevalue("address")
    checkout.save(update_fields=["shipping_address"])
    return request.getfixturevalue("shipping_method")


def delivery_method(request, checkout):
    method = _with_shipping_address(request, checkout)
    return {"deliveryMethodId": graphene.Node.to_global_id("ShippingMethod", method.pk)}


def shipping_method(request, checkout):
    method = _with_shipping_address(request, checkout)
    return {"shippingMethodId": graphene.Node.to_global_id("ShippingMethod", method.pk)}


def email(request, checkout):
    return {"email": "new@example.com"}


def customer_attach(request, checkout):
    return {}


def customer_detach(request, checkout):
    checkout.user = request.getfixturevalue("customer_user")
    checkout.save(update_fields=["user"])
    return {}


def customer_note(request, checkout):
    return {"customerNote": "Leave at the door."}


def language_code(request, checkout):
    return {"languageCode": LanguageCodeEnum.PL.name}


def add_promo_code(request, checkout):
    return {"promoCode": request.getfixturevalue("voucher").code}


def remove_promo_code(request, checkout):
    code = request.getfixturevalue("voucher").code
    checkout.voucher_code = code
    checkout.save(update_fields=["voucher_code"])
    return {"promoCode": code}


@pytest.mark.parametrize(
    ("mutation_name", "arguments", "build_variables"),
    [
        ("checkoutLinesAdd", {"lines": "[CheckoutLineInput!]!"}, lines_add),
        (
            "checkoutLinesUpdate",
            {"lines": "[CheckoutLineUpdateInput!]!"},
            lines_update,
        ),
        ("checkoutLinesDelete", {"linesIds": "[ID!]!"}, lines_delete),
        ("checkoutLineDelete", {"lineId": "ID"}, line_delete),
        (
            "checkoutShippingAddressUpdate",
            {"shippingAddress": "AddressInput!"},
            shipping_address,
        ),
        (
            "checkoutBillingAddressUpdate",
            {"billingAddress": "AddressInput!"},
            billing_address,
        ),
        ("checkoutDeliveryMethodUpdate", {"deliveryMethodId": "ID"}, delivery_method),
        ("checkoutShippingMethodUpdate", {"shippingMethodId": "ID!"}, shipping_method),
        ("checkoutEmailUpdate", {"email": "String!"}, email),
        ("checkoutCustomerAttach", {}, customer_attach),
        ("checkoutCustomerDetach", {}, customer_detach),
        (
            "checkoutCustomerNoteUpdate",
            {"id": "ID!", "customerNote": "String!"},
            customer_note,
        ),
        (
            "checkoutLanguageCodeUpdate",
            {"languageCode": "LanguageCodeEnum!"},
            language_code,
        ),
        ("checkoutAddPromoCode", {"promoCode": "String!"}, add_promo_code),
        ("checkoutRemovePromoCode", {"promoCode": "String"}, remove_promo_code),
    ],
)
def test_marks_customer_change(
    mutation_name,
    arguments,
    build_variables,
    request,
    user_api_client,
    checkout_with_item,
):
    # given
    checkout = checkout_with_item
    assert checkout.last_customer_change is None
    variables = {"id": to_global_id_or_none(checkout)}
    variables.update(build_variables(request, checkout))
    now = timezone.now()

    # when
    with freeze_time(now):
        response = user_api_client.post_graphql(
            build_mutation(mutation_name, arguments), variables
        )

    # then
    content = get_graphql_content(response)
    assert content["data"][mutation_name]["errors"] == []
    checkout.refresh_from_db(fields=["last_customer_change"])
    assert checkout.last_customer_change == now


CHECKOUT_CREATE = """
mutation ($input: CheckoutCreateInput!) {
  checkoutCreate(input: $input) {
    checkout { token }
    errors { field message }
  }
}
"""


def test_checkout_create_marks_customer_change(api_client, stock, channel_USD):
    # given
    variant = stock.product_variant
    variables = {
        "input": {
            "channel": channel_USD.slug,
            "email": "customer@example.com",
            "lines": [
                {
                    "variantId": graphene.Node.to_global_id(
                        "ProductVariant", variant.pk
                    ),
                    "quantity": 1,
                }
            ],
        }
    }
    now = timezone.now()

    # when
    with freeze_time(now):
        response = api_client.post_graphql(CHECKOUT_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert data["errors"] == []
    checkout = Checkout.objects.get(token=data["checkout"]["token"])
    assert checkout.last_customer_change == now


CHECKOUT_CREATE_FROM_ORDER = """
mutation ($id: ID!) {
  checkoutCreateFromOrder(id: $id) {
    checkout { token }
    errors { field message }
  }
}
"""


def test_checkout_create_from_order_marks_customer_change(
    user_api_client, order_with_lines
):
    # given
    order_with_lines.user = user_api_client.user
    order_with_lines.save(update_fields=["user"])
    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.pk)}
    now = timezone.now()

    # when
    with freeze_time(now):
        response = user_api_client.post_graphql(CHECKOUT_CREATE_FROM_ORDER, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreateFromOrder"]
    assert data["errors"] == []
    checkout = Checkout.objects.get(token=data["checkout"]["token"])
    assert checkout.last_customer_change == now
