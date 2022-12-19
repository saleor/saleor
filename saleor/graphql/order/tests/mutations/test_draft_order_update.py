import graphene

from .....order import OrderStatus
from .....order.error_codes import OrderErrorCode
from .....order.models import OrderEvent
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
        $id: ID!, $voucher: ID!, $customerNote: String, $shippingAddress: AddressInput,
        $externalReference: String
    ) {
        draftOrderUpdate(
            id: $id,
            input: {
                voucher: $voucher,
                customerNote: $customerNote,
                shippingAddress: $shippingAddress,
                externalReference: $externalReference
            }) {
            errors {
                field
                message
                code
            }
            order {
                userEmail
                externalReference
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
    external_reference = "test-ext-ref"
    variables = {
        "id": order_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
        "externalReference": external_reference,
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
    assert (
        data["order"]["externalReference"]
        == external_reference
        == order.external_reference
    )


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


DRAFT_ORDER_UPDATE_BY_EXTERNAL_REFERENCE = """
    mutation draftUpdate(
        $id: ID
        $externalReference: String
        $input: DraftOrderInput!
    ) {
        draftOrderUpdate(
            id: $id
            externalReference: $externalReference
            input: $input
        ) {
            errors {
                field
                message
                code
            }
            order {
                id
                externalReference
                voucher {
                    id
                }
            }
        }
    }
    """


def test_draft_order_update_by_external_reference(
    staff_api_client, permission_manage_orders, draft_order, voucher_free_shipping
):
    # given
    query = DRAFT_ORDER_UPDATE_BY_EXTERNAL_REFERENCE

    order = draft_order
    assert not order.voucher
    voucher = voucher_free_shipping
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    ext_ref = "test-ext-ref"
    order.external_reference = ext_ref
    order.save(update_fields=["external_reference"])

    variables = {
        "externalReference": ext_ref,
        "input": {"voucher": voucher_id},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    assert data["order"]["externalReference"] == ext_ref
    assert data["order"]["id"] == graphene.Node.to_global_id("Order", order.id)
    assert data["order"]["voucher"]["id"] == voucher_id
    order.refresh_from_db()
    assert order.voucher


def test_draft_order_update_by_both_id_and_external_reference(
    staff_api_client, permission_manage_orders, voucher_free_shipping
):
    # given
    query = DRAFT_ORDER_UPDATE_BY_EXTERNAL_REFERENCE

    variables = {
        "id": "test-id",
        "externalReference": "test-ext-ref",
        "input": {},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderUpdate"]
    assert not data["order"]
    assert (
        data["errors"][0]["message"]
        == "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_draft_order_update_by_external_reference_not_existing(
    staff_api_client, permission_manage_orders, voucher_free_shipping
):
    # given
    query = DRAFT_ORDER_UPDATE_BY_EXTERNAL_REFERENCE
    ext_ref = "non-existing-ext-ref"
    variables = {
        "externalReference": ext_ref,
        "input": {},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderUpdate"]
    assert not data["order"]
    assert data["errors"][0]["message"] == f"Couldn't resolve to a node: {ext_ref}"


def test_draft_order_update_with_non_unique_external_reference(
    staff_api_client,
    permission_manage_orders,
    draft_order,
    order_list,
):
    # given
    query = DRAFT_ORDER_UPDATE_BY_EXTERNAL_REFERENCE

    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)
    ext_ref = "test-ext-ref"
    order = order_list[1]
    order.external_reference = ext_ref
    order.save(update_fields=["external_reference"])

    variables = {"id": draft_order_id, "input": {"externalReference": ext_ref}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["draftOrderUpdate"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == OrderErrorCode.UNIQUE.name
    assert error["message"] == "Order with this External reference already exists."
