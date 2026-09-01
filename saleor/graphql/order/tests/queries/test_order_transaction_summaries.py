from decimal import Decimal

import graphene
import pytest

from .....payment import PaymentMethodType, TransactionEventType
from .....payment.transaction_item_calculations import (
    recalculate_transaction_amounts,
)
from ....tests.utils import get_graphql_content, get_graphql_content_from_response

ORDER_TRANSACTION_SUMMARIES_QUERY = """
query Order($id: ID!) {
  order(id: $id) {
    transactionSummaries {
      createdAt
      authorizedAmount { amount currency }
      authorizePendingAmount { amount currency }
      chargedAmount { amount currency }
      chargePendingAmount { amount currency }
      refundedAmount { amount currency }
      canceledAmount { amount currency }
      paymentMethodDetails {
        name
        ... on CardPaymentMethodDetails {
          brand
          firstDigits
          lastDigits
          expMonth
          expYear
        }
      }
    }
  }
}
"""


@pytest.mark.parametrize(
    ("api_client_fixture", "grant_manage_orders"),
    [
        ("api_client", False),
        ("user_api_client", False),
        ("staff_api_client", False),
        ("staff_api_client", True),
    ],
)
def test_available_to_any_requester_that_can_resolve_the_order(
    api_client_fixture,
    grant_manage_orders,
    request,
    order,
    transaction_item_generator,
    permission_manage_orders,
):
    # given
    charged_value = Decimal("13.50")
    transaction = transaction_item_generator(
        order_id=order.pk, charged_value=charged_value
    )
    api_client = request.getfixturevalue(api_client_fixture)
    if grant_manage_orders:
        api_client.user.user_permissions.add(permission_manage_orders)
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = api_client.post_graphql(ORDER_TRANSACTION_SUMMARIES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    summaries = content["data"]["order"]["transactionSummaries"]
    assert len(summaries) == 1
    assert summaries[0]["chargedAmount"] == {
        "amount": float(transaction.amount_charged.amount),
        "currency": transaction.currency,
    }
    assert summaries[0]["authorizedAmount"]["amount"] == 0.0
    assert summaries[0]["paymentMethodDetails"] is None


def test_payment_method_details_are_returned(
    api_client, order, transaction_item_generator
):
    # given
    payment_method_name = "Credit card"
    brand = "visa"
    first_digits = "4111"
    last_digits = "1111"
    exp_month = 12
    exp_year = 2035
    transaction_item_generator(
        order_id=order.pk,
        charged_value=Decimal("10.00"),
        payment_method_type=PaymentMethodType.CARD,
        payment_method_name=payment_method_name,
        cc_brand=brand,
        cc_first_digits=first_digits,
        cc_last_digits=last_digits,
        cc_exp_month=exp_month,
        cc_exp_year=exp_year,
    )
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = api_client.post_graphql(ORDER_TRANSACTION_SUMMARIES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    summaries = content["data"]["order"]["transactionSummaries"]
    assert len(summaries) == 1
    assert summaries[0]["paymentMethodDetails"] == {
        "name": payment_method_name,
        "brand": brand,
        "firstDigits": first_digits,
        "lastDigits": last_digits,
        "expMonth": exp_month,
        "expYear": exp_year,
    }


def test_transaction_without_any_money_movement_is_filtered_out(
    api_client, order, transaction_item_generator
):
    # given
    charged_value = Decimal("21.00")
    funded_transaction = transaction_item_generator(
        order_id=order.pk, charged_value=charged_value
    )
    abandoned_transaction = transaction_item_generator(order_id=order.pk)
    assert abandoned_transaction.has_money_movement() is False
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = api_client.post_graphql(ORDER_TRANSACTION_SUMMARIES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    summaries = content["data"]["order"]["transactionSummaries"]
    assert len(summaries) == 1
    assert summaries[0]["chargedAmount"]["amount"] == float(
        funded_transaction.amount_charged.amount
    )


def test_fully_refunded_transaction_is_returned(
    api_client, order, transaction_item_generator, transaction_events_generator
):
    # given
    amount = Decimal("30.00")
    transaction = transaction_item_generator(order_id=order.pk, charged_value=amount)
    transaction_events_generator(
        psp_references=["refund-ref"],
        types=[TransactionEventType.REFUND_SUCCESS],
        amounts=[amount],
        transaction=transaction,
    )
    recalculate_transaction_amounts(transaction)
    assert transaction.charged_value == Decimal(0)
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = api_client.post_graphql(ORDER_TRANSACTION_SUMMARIES_QUERY, variables)

    # then
    content = get_graphql_content(response)
    summaries = content["data"]["order"]["transactionSummaries"]
    assert len(summaries) == 1
    assert summaries[0]["chargedAmount"]["amount"] == 0.0
    assert summaries[0]["refundedAmount"]["amount"] == float(amount)


@pytest.mark.parametrize(
    "field", ["id", "token", "pspReference", "events { id }", "actions", "externalUrl"]
)
def test_internal_fields_are_not_exposed(field, api_client, order):
    # given
    query = f"""
    query Order($id: ID!) {{
      order(id: $id) {{
        transactionSummaries {{ {field} }}
      }}
    }}
    """
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    field_name = field.split(" ")[0]
    assert content["errors"][0]["message"] == (
        f'Cannot query field "{field_name}" on type "TransactionSummary".'
    )
