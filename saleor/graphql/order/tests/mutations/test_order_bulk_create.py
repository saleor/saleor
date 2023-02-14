from .....order.models import Order
from .....tests.utils import flush_post_commit_hooks
from ....tests.utils import get_graphql_content

ORDER_BULK_CREATE = """
    mutation OrderBulkCreate(
        $orders: [ProductVariantBulkCreateInput!]!,
        $errorPolicy: ErrorPolicyEnum
    ) {
        orderBulkCreate(orders: $orders, errorPolicy: $errorPolicy) {
            count
            results {
                order {
                    id
                    discount {
                        amount
                    }
                    discountName
                    redirectUrl
                    lines {
                        productName
                        productSku
                        quantity
                    }
                    billingAddress{
                        city
                        streetAddress1
                        postalCode
                    }
                    shippingAddress{
                        city
                        streetAddress1
                        postalCode
                    }
                    status
                    voucher {
                        code
                    }
                    customerNote
                    total {
                        gross {
                            amount
                        }
                    }
                    shippingMethodName
                    externalReference
                }
                errors {
                    field
                    message
                    code
                    warehouses
                    channels
                }
            }
        }
    }
"""


def test_order_bulk_create(
    staff_api_client,
    permission_manage_orders,
):
    # given
    # orders_count = Order.objects.count()
    # orders = [{}]

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    variables = {}

    # when

    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)
    flush_post_commit_hooks()

    # then
    data = content["data"]["orderBulkCreate"]
    assert not data["results"][0]["errors"]
