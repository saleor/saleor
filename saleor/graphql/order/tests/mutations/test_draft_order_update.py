import graphene
from prices import Money

from .....order import OrderStatus
from .....order.error_codes import OrderErrorCode
from .....order.models import OrderEvent
from ....account.tests.utils import convert_dict_keys_to_camel_case
from ....tests.utils import get_graphql_content

DRAFT_UPDATE_QUERY = """
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
                    userEmail
                    channel {
                        id
                    }
                }
            }
        }
        """


def test_draft_order_update_existing_channel_id(
    staff_api_client, permission_manage_orders, order_with_lines, channel_PLN
):
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save()
    query = DRAFT_UPDATE_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": order_id,
        "input": {
            "channelId": channel_id,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderUpdate"]["errors"][0]

    assert error["code"] == OrderErrorCode.NOT_EDITABLE.name
    assert error["field"] == "channelId"


def test_draft_order_update_voucher_not_available(
    staff_api_client, permission_manage_orders, order_with_lines, voucher
):
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save()
    assert order.voucher is None
    query = DRAFT_UPDATE_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    voucher.channel_listings.all().delete()
    variables = {
        "id": order_id,
        "input": {
            "voucher": voucher_id,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderUpdate"]["errors"][0]

    assert error["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert error["field"] == "voucher"


DRAFT_ORDER_UPDATE_MUTATION = """
    mutation draftUpdate(
        $id: ID!, $voucher: ID!, $customerNote: String, $shippingAddress: AddressInput
    ) {
        draftOrderUpdate(id: $id,
                            input: {
                                voucher: $voucher,
                                customerNote: $customerNote,
                                shippingAddress: $shippingAddress,
                            }) {
            errors {
                field
                message
                code
            }
            order {
                userEmail
            }
        }
    }
"""


def test_draft_order_update(
    staff_api_client, permission_manage_orders, draft_order, voucher
):
    order = draft_order
    assert not order.voucher
    assert not order.customer_note
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    customer_note = "Test customer note"
    variables = {
        "id": order_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    order.refresh_from_db()
    assert order.voucher
    assert order.customer_note == customer_note
    assert order.search_vector


def test_draft_order_update_with_non_draft_order(
    staff_api_client, permission_manage_orders, order_with_lines, voucher
):
    order = order_with_lines
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    customer_note = "Test customer note"
    variables = {"id": order_id, "voucher": voucher_id, "customerNote": customer_note}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderUpdate"]["errors"][0]
    assert error["field"] == "id"
    assert error["code"] == OrderErrorCode.INVALID.name


def test_draft_order_update_invalid_address(
    staff_api_client,
    permission_manage_orders,
    draft_order,
    voucher,
    graphql_address_data,
):
    order = draft_order
    assert not order.voucher
    assert not order.customer_note
    graphql_address_data["postalCode"] = "TEST TEST invalid postal code 12345"
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)

    variables = {
        "id": order_id,
        "voucher": voucher_id,
        "shippingAddress": graphql_address_data,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert len(data["errors"]) == 2
    assert not data["order"]
    assert {error["code"] for error in data["errors"]} == {
        OrderErrorCode.INVALID.name,
        OrderErrorCode.REQUIRED.name,
    }
    assert {error["field"] for error in data["errors"]} == {"postalCode"}


def test_draft_order_update_doing_nothing_generates_no_events(
    staff_api_client, permission_manage_orders, order_with_lines
):
    assert not OrderEvent.objects.exists()

    query = """
        mutation draftUpdate($id: ID!) {
            draftOrderUpdate(id: $id, input: {}) {
                errors {
                    field
                    message
                }
            }
        }
        """
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    response = staff_api_client.post_graphql(
        query, {"id": order_id}, permissions=[permission_manage_orders]
    )
    get_graphql_content(response)

    # Ensure not event was created
    assert not OrderEvent.objects.exists()


def test_draft_order_update_free_shipping_voucher(
    staff_api_client, permission_manage_orders, draft_order, voucher_free_shipping
):
    order = draft_order
    assert not order.voucher
    query = """
        mutation draftUpdate(
            $id: ID!
            $voucher: ID!
        ) {
            draftOrderUpdate(
                id: $id
                input: {
                    voucher: $voucher
                }
            ) {
                errors {
                    field
                    message
                    code
                }
                order {
                    id
                }
            }
        }
        """
    voucher = voucher_free_shipping
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    variables = {
        "id": order_id,
        "voucher": voucher_id,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    assert data["order"]["id"] == variables["id"]
    order.refresh_from_db()
    assert order.voucher


DRAFT_ORDER_UPDATE_USER_EMAIL_MUTATION = """
    mutation draftUpdate(
        $id: ID!
        $userEmail: String!
    ) {
        draftOrderUpdate(
            id: $id
            input: {
                userEmail: $userEmail
            }
        ) {
            errors {
                field
                message
                code
            }
            order {
                id
            }
        }
    }
    """


def test_draft_order_update_when_not_existing_customer_email_provided(
    staff_api_client, permission_manage_orders, draft_order
):
    # given
    order = draft_order
    assert order.user

    query = DRAFT_ORDER_UPDATE_USER_EMAIL_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    email = "notexisting@example.com"
    variables = {"id": order_id, "userEmail": email}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    order.refresh_from_db()

    # then
    assert not data["errors"]
    assert not order.user
    assert order.user_email == email


def test_draft_order_update_assign_user_when_existing_customer_email_provided(
    staff_api_client, permission_manage_orders, draft_order
):
    # given
    order = draft_order
    user = order.user
    user_email = user.email
    order.user = None
    order.save(update_fields=["user"])
    assert not order.user

    query = DRAFT_ORDER_UPDATE_USER_EMAIL_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "userEmail": user_email}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    order.refresh_from_db()

    # then
    assert not data["errors"]
    assert order.user == user
    assert order.user_email == user_email


DRAFT_ORDER_UPDATE_SHIPPING_METHOD_MUTATION = """
    mutation draftUpdate(
        $id: ID!, $shippingMethod: ID
    ) {
        draftOrderUpdate(id: $id,
                            input: {
                                shippingMethod: $shippingMethod
                            }) {
            errors {
                field
                message
                code
            }
            order {
                shippingMethodName
                shippingPrice {
                tax {
                    amount
                    }
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
            shippingTaxRate
            }
        }
    }
"""


def test_draft_order_update_shipping_method_from_different_channel(
    staff_api_client,
    permission_manage_orders,
    draft_order,
    address_usa,
    shipping_method_channel_PLN,
):
    # given
    order = draft_order
    order.shipping_address = address_usa
    order.save(update_fields=["shipping_address"])
    query = DRAFT_ORDER_UPDATE_SHIPPING_METHOD_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method_channel_PLN.id
    )
    variables = {"id": order_id, "shippingMethod": shipping_method_id}
    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )

    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]

    # then
    assert len(data["errors"]) == 1
    assert not data["order"]
    error = data["errors"][0]
    assert error["code"] == OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert error["field"] == "shippingMethod"


def test_draft_order_update_shipping_method_prices_updates(
    staff_api_client,
    permission_manage_orders,
    draft_order,
    address_usa,
    shipping_method,
    shipping_method_weight_based,
):
    # given
    order = draft_order
    order.shipping_address = address_usa
    order.shipping_method = shipping_method
    order.save(update_fields=["shipping_address", "shipping_method"])
    assert shipping_method.channel_listings.first().price_amount == 10
    method_2 = shipping_method_weight_based
    m2_channel_listing = method_2.channel_listings.first()
    m2_channel_listing.price_amount = 15
    m2_channel_listing.save(update_fields=["price_amount"])
    query = DRAFT_ORDER_UPDATE_SHIPPING_METHOD_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    shipping_method_id = graphene.Node.to_global_id("ShippingMethod", method_2.id)
    variables = {"id": order_id, "shippingMethod": shipping_method_id}
    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )

    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    order.refresh_from_db()

    # then
    assert not data["errors"]
    assert data["order"]["shippingMethodName"] == method_2.name
    assert data["order"]["shippingPrice"]["net"]["amount"] == 15.0


DRAFT_ORDER_UPDATE_SHIPPING_ADDRESS_MUTATION = """
    mutation draftUpdate(
        $id: ID!, $shippingAddress: AddressInput
    ) {
        draftOrderUpdate(id: $id,
                            input: {
                                shippingAddress: $shippingAddress
                            }) {
            errors {
                field
                message
                code
            }
            order {
                shippingMethodName
                shippingPrice {
                tax {
                    amount
                    }
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
            shippingTaxRate
            }
        }
    }
"""


def test_draft_order_update_address_clear_invalid_shipping_method(
    staff_api_client,
    permission_manage_orders,
    draft_order,
    address_usa,
    shipping_method,
    address,
):
    # given
    order = draft_order
    order.shipping_address = address_usa
    order.shipping_method = shipping_method
    order.save(update_fields=["shipping_address", "shipping_method"])
    query = DRAFT_ORDER_UPDATE_SHIPPING_ADDRESS_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    address_data = convert_dict_keys_to_camel_case(address.as_data())

    variables = {"id": order_id, "shippingAddress": address_data}
    zero_shipping_price_data = {
        "tax": {"amount": 0.0},
        "net": {"amount": 0.0},
        "gross": {"amount": 0.0},
    }
    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )

    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    order.refresh_from_db()

    # then
    assert not data["errors"]
    assert data["order"]["shippingMethodName"] is None
    assert data["order"]["shippingPrice"] == zero_shipping_price_data
    assert data["order"]["shippingTaxRate"] == 0.0
    assert order.shipping_method is None
