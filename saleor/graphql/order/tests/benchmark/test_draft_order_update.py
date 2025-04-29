import graphene
import pytest

from .....order import OrderStatus
from ....core.enums import LanguageCodeEnum
from ....tests.utils import get_graphql_content

DRAFT_ORDER_UPDATE_MUTATION = """
    mutation draftUpdate(
    $id: ID!,
    $input: DraftOrderInput!,
    ) {
        draftOrderUpdate(
            id: $id,
            input: $input
        ) {
            errors {
                field
                code
                message
            }
            order {
                id
            }
        }
    }
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_draft_order_update(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    voucher,
    address,
    customer_user,
    shipping_method,
    graphql_address_data,
    count_queries,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])
    order_id = graphene.Node.to_global_id("Order", order.id)

    key = "some_key"
    value = "some_value"

    order.metadata = {key: value}
    order.private_metadata = {key: value}
    order.shipping_address = address
    order.billing_address = address
    order.shipping_method_id = None
    order.draft_save_billing_address = False
    order.draft_save_shipping_address = False
    order.voucher = None
    order.voucher_code = None
    order.customer_note = "some note"
    order.redirect_url = "http://localhost:8000/redirect"
    order.external_reference = "some_reference_string"
    order.language_code = "pl"
    order.save()

    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.id
    )
    user_id = graphene.Node.to_global_id("User", customer_user.id)

    input = {
        "billingAddress": graphql_address_data,
        "saveBillingAddress": True,
        "shippingAddress": graphql_address_data,
        "saveShippingAddress": True,
        "shippingMethod": shipping_method_id,
        "user": user_id,
        "userEmail": customer_user.email,
        "voucherCode": voucher.codes.first().code,
        "customerNote": "new note",
        "redirectUrl": "https://www.example.com",
        "externalReference": "new_reference",
        "metadata": [{"key": "new_key", "value": "new_value"}],
        "privateMetadata": [{"key": "new_key", "value": "new_value"}],
        "languageCode": LanguageCodeEnum.DE.name,
    }

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"id": order_id, "input": input}

    # when
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_UPDATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderUpdate"]["errors"]
