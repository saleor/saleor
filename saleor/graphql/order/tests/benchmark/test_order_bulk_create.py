from decimal import Decimal

import graphene
import pytest
from django.utils import timezone

from ....discount.enums import DiscountValueTypeEnum
from ....tests.utils import get_graphql_content
from ..mutations.test_order_bulk_create import (  # noqa F401
    ORDER_BULK_CREATE,
    order_bulk_input,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_order_bulk_create(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,  # noqa F881
    product_variant_list,
    customer_user,
    app,
    count_queries,
):
    # given
    order_1 = order_2 = order_bulk_input_with_multiple_order_lines_and_fulfillments

    note_1 = {
        "message": "User message",
        "date": timezone.now(),
        "userId": graphene.Node.to_global_id("User", customer_user.id),
    }
    note_2 = {
        "message": "App message",
        "date": timezone.now(),
        "appId": graphene.Node.to_global_id("App", app.id),
    }
    order_2["notes"] = [note_1, note_2]

    transaction_1 = {
        "name": "Authorized for 10$",
        "amountAuthorized": {
            "amount": Decimal("20"),
            "currency": "PLN",
        },
    }

    transaction_2 = {
        "name": "Credit Card",
        "amountCharged": {
            "amount": Decimal("100"),
            "currency": "PLN",
        },
    }
    order_2["transactions"] = [transaction_1, transaction_2]

    invoice_1 = {
        "number": "01/12/2020/TEST",
        "createdAt": timezone.now(),
    }
    invoice_2 = {
        "url": "http://www.example2.com",
        "createdAt": timezone.now(),
    }
    order_2["invoices"] = [invoice_1, invoice_2]

    discount_1 = {
        "valueType": DiscountValueTypeEnum.FIXED.name,
        "value": 10,
    }
    discount_2 = {
        "valueType": DiscountValueTypeEnum.PERCENTAGE.name,
        "value": 101,
    }
    order_2["discounts"] = [discount_1, discount_2]

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {"orders": [order_1, order_2]}

    # when & then
    get_graphql_content(staff_api_client.post_graphql(ORDER_BULK_CREATE, variables))
