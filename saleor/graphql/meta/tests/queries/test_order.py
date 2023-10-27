import graphene

from .....order.models import Order
from .....permission.models import Permission
from ....tests.fixtures import ApiClient
from ....tests.utils import assert_no_permission, get_graphql_content
from .utils import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE, execute_query

QUERY_ORDER_BY_TOKEN_PUBLIC_META = """
    query orderMeta($token: UUID!){
        orderByToken(token: $token){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_order_by_token_as_anonymous_user(api_client, order):
    # given
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["metadata"])
    variables = {"token": order.id}

    # when
    response = api_client.post_graphql(QUERY_ORDER_BY_TOKEN_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_order_by_token_as_customer(user_api_client, order):
    # given
    order.user = user_api_client.user
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "metadata"])
    variables = {"token": order.id}

    # when
    response = user_api_client.post_graphql(QUERY_ORDER_BY_TOKEN_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_order_by_token_as_staff(
    staff_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "metadata"])
    variables = {"token": order.id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_BY_TOKEN_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_order_by_token_as_app(
    app_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "metadata"])
    variables = {"token": order.id}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_BY_TOKEN_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_ORDER_PUBLIC_META = """
    query orderMeta($id: ID!){
        order(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_order_as_anonymous_user(api_client, order):
    # given
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = api_client.post_graphql(QUERY_ORDER_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_order_as_customer(user_api_client, order):
    # given
    order.user = user_api_client.user
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_ORDER_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_order_as_staff(
    staff_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_order_as_app(
    app_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_DRAFT_ORDER_PUBLIC_META = """
    query draftOrderMeta($id: ID!){
        order(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_draft_order_as_anonymous_user(api_client, draft_order):
    # given
    draft_order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    draft_order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = api_client.post_graphql(QUERY_DRAFT_ORDER_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_draft_order_as_customer(user_api_client, draft_order):
    # given
    draft_order.user = user_api_client.user
    draft_order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    draft_order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_DRAFT_ORDER_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_draft_order_as_staff(
    staff_api_client, draft_order, customer_user, permission_manage_orders
):
    # given
    draft_order.user = customer_user
    draft_order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    draft_order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDER_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_draft_order_as_app(
    app_api_client, draft_order, customer_user, permission_manage_orders
):
    # given
    draft_order.user = customer_user
    draft_order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    draft_order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_FULFILLMENT_PUBLIC_META = """
    query fulfillmentMeta($token: UUID!){
        orderByToken(token: $token){
            fulfillments{
                metadata{
                    key
                    value
                }
          }
        }
    }
"""


def test_query_public_meta_for_fulfillment_as_anonymous_user(
    api_client, fulfilled_order
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["metadata"])
    variables = {"token": fulfilled_order.id}

    # when
    response = api_client.post_graphql(QUERY_FULFILLMENT_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["fulfillments"][0]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_fulfillment_as_customer(
    user_api_client, fulfilled_order
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["metadata"])
    fulfilled_order.user = user_api_client.user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.id}

    # when
    response = user_api_client.post_graphql(QUERY_FULFILLMENT_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["fulfillments"][0]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_fulfillment_as_staff(
    staff_api_client, fulfilled_order, customer_user, permission_manage_orders
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["metadata"])
    fulfilled_order.user = customer_user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_FULFILLMENT_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["fulfillments"][0]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_fulfillment_as_app(
    app_api_client, fulfilled_order, customer_user, permission_manage_orders
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["metadata"])
    fulfilled_order.user = customer_user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.id}

    # when
    response = app_api_client.post_graphql(
        QUERY_FULFILLMENT_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["fulfillments"][0]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_ORDER_BY_TOKEN_PRIVATE_META = """
    query orderMeta($token: UUID!){
        orderByToken(token: $token){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_order_by_token_as_anonymous_user(api_client, order):
    # given
    variables = {"token": order.id}

    # when
    response = api_client.post_graphql(QUERY_ORDER_BY_TOKEN_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_order_by_token_as_customer(user_api_client, order):
    # given
    order.user = user_api_client.user
    order.save(update_fields=["user"])
    variables = {"token": order.id}

    # when
    response = user_api_client.post_graphql(
        QUERY_ORDER_BY_TOKEN_PRIVATE_META, variables
    )

    # then
    assert_no_permission(response)


def test_query_private_meta_for_order_by_token_as_staff(
    staff_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["user", "private_metadata"])
    variables = {"token": order.id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_BY_TOKEN_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_order_by_token_as_app(
    app_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["user", "private_metadata"])
    variables = {"token": order.id}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_BY_TOKEN_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_ORDER_PRIVATE_META = """
    query orderMeta($id: ID!){
        order(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_order_as_anonymous_user(api_client, order):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = api_client.post_graphql(QUERY_ORDER_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_order_as_customer(user_api_client, order):
    # given
    order.user = user_api_client.user
    order.save(update_fields=["user"])
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_ORDER_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_order_as_staff(
    staff_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["user", "private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_order_as_app(
    app_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["user", "private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_DRAFT_ORDER_PRIVATE_META = """
    query draftOrderMeta($id: ID!){
        order(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_draft_order_as_anonymous_user(api_client, draft_order):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = api_client.post_graphql(QUERY_DRAFT_ORDER_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_draft_order_as_customer(user_api_client, draft_order):
    # given
    draft_order.user = user_api_client.user
    draft_order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    draft_order.save(update_fields=["user", "private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_DRAFT_ORDER_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_draft_order_as_staff(
    staff_api_client, draft_order, customer_user, permission_manage_orders
):
    # given
    draft_order.user = customer_user
    draft_order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    draft_order.save(update_fields=["user", "private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDER_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_draft_order_as_app(
    app_api_client, draft_order, customer_user, permission_manage_orders
):
    # given
    draft_order.user = customer_user
    draft_order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    draft_order.save(update_fields=["user", "private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_FULFILLMENT_PRIVATE_META = """
    query fulfillmentMeta($token: UUID!){
        orderByToken(token: $token){
            fulfillments{
                privateMetadata{
                    key
                    value
                }
          }
        }
    }
"""


def test_query_private_meta_for_fulfillment_as_anonymous_user(
    api_client, fulfilled_order
):
    # given
    variables = {"token": fulfilled_order.id}

    # when
    response = api_client.post_graphql(QUERY_FULFILLMENT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_fulfillment_as_customer(
    user_api_client, fulfilled_order
):
    # given
    fulfilled_order.user = user_api_client.user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.id}

    # when
    response = user_api_client.post_graphql(QUERY_FULFILLMENT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_fulfillment_as_staff(
    staff_api_client, fulfilled_order, customer_user, permission_manage_orders
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    fulfillment.save(update_fields=["private_metadata"])
    fulfilled_order.user = customer_user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_FULFILLMENT_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["fulfillments"][0]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_fulfillment_as_app(
    app_api_client, fulfilled_order, customer_user, permission_manage_orders
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    fulfillment.save(update_fields=["private_metadata"])
    fulfilled_order.user = customer_user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.id}

    # when
    response = app_api_client.post_graphql(
        QUERY_FULFILLMENT_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["fulfillments"][0]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_TRANSACTION_ITEM_PUBLIC_META = """
query transactionItemMeta($id: ID!){
  order(id: $id){
    transactions{
      metadata{
        key
        value
      }
    }
  }
}
"""


def execute_query_public_metadata_for_transaction_item(
    client: ApiClient, order: Order, permissions: list[Permission] = None
):
    return execute_query(
        QUERY_TRANSACTION_ITEM_PUBLIC_META, client, order, "Order", permissions
    )


def assert_transaction_item_contains_metadata(response):
    content = get_graphql_content(response)
    metadata = content["data"]["order"]["transactions"][0]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_transaction_item_as_customer(
    user_api_client, order, permission_manage_orders
):
    # given
    order.payment_transactions.create(metadata={PUBLIC_KEY: PUBLIC_VALUE})
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["metadata"])

    # when
    response = execute_query_public_metadata_for_transaction_item(
        user_api_client,
        order,
        permissions=[],
    )

    # then
    assert_no_permission(response)


def test_query_public_meta_for_transaction_item_as_staff_with_permission(
    staff_api_client,
    order_with_lines,
    permission_manage_orders,
    permission_manage_payments,
):
    # given
    order_with_lines.payment_transactions.create(metadata={PUBLIC_KEY: PUBLIC_VALUE})

    # when
    response = execute_query_public_metadata_for_transaction_item(
        staff_api_client,
        order_with_lines,
        permissions=[permission_manage_orders, permission_manage_payments],
    )

    # then
    assert_transaction_item_contains_metadata(response)


def test_query_public_meta_for_transaction_item_as_staff_without_permission(
    staff_api_client, order
):
    # given
    order.payment_transactions.create(metadata={PUBLIC_KEY: PUBLIC_VALUE})

    # when
    response = execute_query_public_metadata_for_transaction_item(
        staff_api_client, order
    )

    # then
    assert_no_permission(response)


def test_query_public_meta_for_transaction_item_as_app_with_permission(
    app_api_client,
    order,
    permission_manage_orders,
    permission_manage_payments,
):
    order.payment_transactions.create(metadata={PUBLIC_KEY: PUBLIC_VALUE})

    # when
    response = execute_query_public_metadata_for_transaction_item(
        app_api_client,
        order,
        permissions=[permission_manage_payments, permission_manage_orders],
    )

    # then
    assert_transaction_item_contains_metadata(response)


def test_query_public_meta_for_transaction_item_as_app_without_permission(
    app_api_client, order
):
    # when
    response = execute_query_public_metadata_for_transaction_item(app_api_client, order)

    # then
    assert_no_permission(response)


QUERY_TRANSACTION_ITEM_PRIVATE_META = """
query transactionItemMeta($id: ID!){
  order(id: $id){
    transactions{
      privateMetadata{
        key
        value
      }
    }
  }
}
"""


def execute_query_private_metadata_for_transaction_item(
    client: ApiClient, order: Order, permissions: list[Permission] = None
):
    return execute_query(
        QUERY_TRANSACTION_ITEM_PRIVATE_META, client, order, "Order", permissions
    )


def assert_transaction_item_contains_private_metadata(response):
    content = get_graphql_content(response)
    metadata = content["data"]["order"]["transactions"][0]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_transaction_item_as_customer(
    user_api_client, order, permission_manage_orders
):
    # given
    order.payment_transactions.create(private_metadata={PRIVATE_KEY: PRIVATE_VALUE})

    # when
    response = execute_query_public_metadata_for_transaction_item(
        user_api_client,
        order,
        permissions=[],
    )

    # then
    assert_no_permission(response)


#


def test_query_private_meta_for_transaction_item_as_staff_with_permission(
    staff_api_client,
    order_with_lines,
    permission_manage_orders,
    permission_manage_payments,
):
    # given
    order_with_lines.payment_transactions.create(
        private_metadata={PRIVATE_KEY: PRIVATE_VALUE}
    )

    # when
    response = execute_query_private_metadata_for_transaction_item(
        staff_api_client,
        order_with_lines,
        permissions=[permission_manage_orders, permission_manage_payments],
    )

    # then
    assert_transaction_item_contains_private_metadata(response)


def test_query_private_meta_for_transaction_item_as_staff_without_permission(
    staff_api_client, order
):
    # given
    order.payment_transactions.create(private_metadata={PRIVATE_KEY: PRIVATE_VALUE})

    # when
    response = execute_query_private_metadata_for_transaction_item(
        staff_api_client, order
    )

    # then
    assert_no_permission(response)


def test_query_private_meta_for_transaction_item_as_app_with_permission(
    app_api_client,
    order,
    permission_manage_orders,
    permission_manage_payments,
):
    order.payment_transactions.create(private_metadata={PRIVATE_KEY: PRIVATE_VALUE})

    # when
    response = execute_query_private_metadata_for_transaction_item(
        app_api_client,
        order,
        permissions=[permission_manage_payments, permission_manage_orders],
    )

    # then
    assert_transaction_item_contains_private_metadata(response)


def test_query_private_meta_for_transaction_item_as_app_without_permission(
    app_api_client, order
):
    # when
    response = execute_query_private_metadata_for_transaction_item(
        app_api_client, order
    )

    # then
    assert_no_permission(response)
