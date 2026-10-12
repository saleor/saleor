"""Known gaps in the READ permission model (adversarial review findings).

Every test here asserts the CURRENT, WRONG behavior so it passes today and
documents the bug. Each test carries a `SUGGESTED OUTCOME` comment describing what
it should assert once the implementation is fixed — flip the `then` block to that
outcome when fixing, and the test becomes the regression test.

Findings:
  1. READ_X leaks writes through bearer values (checkout ID, gift card code)
  2. MANAGE_X ⊇ READ_X applied on grant only, not on manage/scope checks
  3. MANAGE-gated read sites that were never widened with expand_read_permissions
  4. Webhook subscriber lookup matches the exact MANAGE_X codename only
"""

import graphene

from ....account import CustomerEvents
from ....account.error_codes import AccountErrorCode, PermissionGroupErrorCode
from ....account.models import CustomerEvent, Group
from ....order import OrderStatus
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...core.enums import PermissionEnum
from ...tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

# --------------------------------------------------------------------------- #
# 1. READ_X leaks writes through bearer values
# --------------------------------------------------------------------------- #

CHECKOUTS_LIST_QUERY = """
    query {
        checkouts(first: 20) {
            edges { node { id } }
        }
    }
"""

CHECKOUT_EMAIL_UPDATE_MUTATION = """
    mutation ($id: ID!, $email: String!) {
        checkoutEmailUpdate(id: $id, email: $email) {
            checkout { email }
            errors { field code message }
        }
    }
"""


def test_read_checkouts_app_can_update_email_of_listed_checkout(
    app_api_client, checkout, permission_read_checkouts
):
    # Scenario: an app holding ONLY READ_CHECKOUTS lists checkouts (the list is
    # widened to READ twins). The checkout ID is a bearer credential: public
    # checkout mutations (checkoutEmailUpdate, checkoutShippingAddressUpdate,
    # checkoutLinesAdd, ...) need nothing but the ID. So "read-only" access to
    # checkouts is in practice write access to every customer's checkout.
    #
    # SUGGESTED OUTCOME: READ_CHECKOUTS must not enable writes. Either keep the
    # `checkouts` list MANAGE_CHECKOUTS-only (then: listing is denied), or
    # document READ_CHECKOUTS as a write-capable permission and drop the
    # read-only claim from read_permissions.py. With the first option this test
    # asserts `assert_no_permission` on the list and the email stays unchanged.

    # given an app holding only READ_CHECKOUTS
    app_api_client.app.permissions.add(permission_read_checkouts)
    original_email = checkout.email
    new_email = "attacker@example.com"

    # when the app lists checkouts and reuses a returned ID in a public mutation
    list_response = app_api_client.post_graphql(CHECKOUTS_LIST_QUERY)
    list_content = get_graphql_content(list_response)
    checkout_id = list_content["data"]["checkouts"]["edges"][0]["node"]["id"]
    response = app_api_client.post_graphql(
        CHECKOUT_EMAIL_UPDATE_MUTATION, {"id": checkout_id, "email": new_email}
    )

    # then (WRONG) the customer's checkout email is overwritten
    content = get_graphql_content(response)
    assert content["data"]["checkoutEmailUpdate"]["errors"] == []
    checkout.refresh_from_db(fields=["email"])
    assert checkout.email == new_email
    assert checkout.email != original_email


GIFT_CARD_CODE_QUERY = """
    query ($id: ID!) {
        giftCard(id: $id) { code }
    }
"""

CHECKOUT_ADD_PROMO_CODE_MUTATION = """
    mutation ($id: ID!, $promoCode: String!) {
        checkoutAddPromoCode(id: $id, promoCode: $promoCode) {
            checkout { giftCards { id } }
            errors { field code message }
        }
    }
"""


def test_read_gift_card_reads_full_code_and_spends_it(
    staff_api_client,
    api_client,
    gift_card,
    checkout_with_item,
    permission_read_gift_card,
):
    # Scenario: a staff user holding ONLY READ_GIFT_CARD reads the full
    # `GiftCard.code` (resolve_code widens MANAGE_GIFT_CARD to its READ twin).
    # The code is a bearer credential: anyone can attach it to a checkout via the
    # public checkoutAddPromoCode and spend the balance.
    #
    # SUGGESTED OUTCOME: keep `GiftCard.code` gated on MANAGE_GIFT_CARD (or
    # owner) only — do not wrap it in expand_read_permissions. READ_GIFT_CARD
    # holders still see `last4CodeChars` / `displayCode`. Then: the code query
    # returns PermissionDenied for this user and the gift card is never attached.
    # Note: `test_read_gift_card_reads_code` in giftcard/tests/test_read_permissions.py
    # pins the current behavior and must be flipped alongside this test.

    # given a non-owner staff user holding only READ_GIFT_CARD
    staff_api_client.user.user_permissions.add(permission_read_gift_card)
    assert gift_card.used_by_id != staff_api_client.user.pk
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when the staff user reads the code and then spends it on any checkout
    code_response = staff_api_client.post_graphql(
        GIFT_CARD_CODE_QUERY, {"id": gift_card_id}
    )
    code = get_graphql_content(code_response)["data"]["giftCard"]["code"]
    response = api_client.post_graphql(
        CHECKOUT_ADD_PROMO_CODE_MUTATION,
        {
            "id": graphene.Node.to_global_id("Checkout", checkout_with_item.pk),
            "promoCode": code,
        },
    )

    # then (WRONG) the full code was exposed and the gift card got attached
    assert code == gift_card.code
    content = get_graphql_content(response)
    data = content["data"]["checkoutAddPromoCode"]
    assert data["errors"] == []
    assert data["checkout"]["giftCards"] == [{"id": gift_card_id}]


# --------------------------------------------------------------------------- #
# 2. MANAGE_X ⊇ READ_X applied on grant only, not on manage/scope checks
# --------------------------------------------------------------------------- #

PERMISSION_GROUP_CREATE_MUTATION = """
    mutation ($input: PermissionGroupCreateInput!) {
        permissionGroupCreate(input: $input) {
            group { id userCanManage }
            errors { field code message }
        }
    }
"""

PERMISSION_GROUP_UPDATE_MUTATION = """
    mutation ($id: ID!, $input: PermissionGroupUpdateInput!) {
        permissionGroupUpdate(id: $id, input: $input) {
            group { id name }
            errors { field code message }
        }
    }
"""

STAFF_UPDATE_MUTATION = """
    mutation ($id: ID!, $input: StaffUpdateInput!) {
        staffUpdate(id: $id, input: $input) {
            user { firstName }
            errors { field code message }
        }
    }
"""


def _give_unrestricted_group(user, *permissions):
    """Put `user` in a channel-unrestricted group holding `permissions`.

    Keeps the channel scope check out of the way so only the permission scope
    check decides whether the user can manage a group / staff member.
    """
    group = Group.objects.create(
        name=f"Scope of {user.email}", restricted_access_to_channels=False
    )
    group.permissions.add(*permissions)
    group.user_set.add(user)
    return group


def test_staff_creates_read_twin_group_then_cannot_manage_it(
    staff_api_client, permission_manage_staff, permission_manage_orders
):
    # Scenario: staff A holds MANAGE_STAFF + MANAGE_ORDERS but not READ_ORDERS.
    # permissionGroupCreate(addPermissions: [READ_ORDERS]) succeeds, because
    # get_out_of_scope_permissions treats MANAGE_ORDERS as covering READ_ORDERS.
    # The group is then locked: can_user_manage_group_permissions compares
    # literal permissions (user.has_perms), so A gets userCanManage=false and
    # permissionGroupUpdate / permissionGroupDelete fail with
    # OUT_OF_SCOPE_PERMISSION on a group A just created.
    #
    # SUGGESTED OUTCOME: route every scope check through one helper that treats
    # a held MANAGE_X as covering READ_X (e.g. can_user_manage_group_permissions
    # returns `not get_out_of_scope_permissions(...)`, and
    # get_groups_which_user_can_manage adds the READ-twin PKs of held MANAGE
    # perms). Then: userCanManage is True and the update returns no errors and
    # renames the group.

    # given staff A with MANAGE_STAFF + MANAGE_ORDERS and no READ_ORDERS
    staff_user = staff_api_client.user
    _give_unrestricted_group(
        staff_user, permission_manage_staff, permission_manage_orders
    )
    assert staff_user.has_perm("order.read_orders") is False
    new_name = "Renamed"

    # when A creates a group holding READ_ORDERS and then renames it
    create_response = staff_api_client.post_graphql(
        PERMISSION_GROUP_CREATE_MUTATION,
        {
            "input": {
                "name": "Read orders",
                "addPermissions": [PermissionEnum.READ_ORDERS.name],
            }
        },
    )
    create_data = get_graphql_content(create_response)["data"]["permissionGroupCreate"]
    update_response = staff_api_client.post_graphql(
        PERMISSION_GROUP_UPDATE_MUTATION,
        {"id": create_data["group"]["id"], "input": {"name": new_name}},
    )

    # then (WRONG) creation succeeds but A cannot manage the group it created
    assert create_data["errors"] == []
    assert create_data["group"]["userCanManage"] is False
    update_data = get_graphql_content(update_response)["data"]["permissionGroupUpdate"]
    assert len(update_data["errors"]) == 1
    assert (
        update_data["errors"][0]["code"]
        == PermissionGroupErrorCode.OUT_OF_SCOPE_PERMISSION.name
    )
    assert update_data["errors"][0]["message"] == (
        "You can't manage group with permissions out of your scope."
    )
    _, group_pk = graphene.Node.from_global_id(create_data["group"]["id"])
    group = Group.objects.get(pk=group_pk)
    assert group.name != new_name


def test_staff_with_manage_twin_cannot_update_read_twin_member(
    staff_api_client,
    staff_users,
    permission_manage_staff,
    permission_manage_orders,
    permission_read_orders,
):
    # Scenario: staff A holds MANAGE_STAFF + MANAGE_ORDERS. Staff member B holds
    # only READ_ORDERS (a strict subset of A's effective scope). staffUpdate on
    # B fails with OUT_OF_SCOPE_USER, because get_out_of_scope_users checks
    # `root_user.has_perms(member_permissions)` literally — MANAGE_ORDERS is not
    # treated as covering READ_ORDERS. Same root cause as the test above; also
    # affects staffDelete.
    #
    # SUGGESTED OUTCOME: get_out_of_scope_users treats MANAGE_X as covering
    # READ_X (reuse get_out_of_scope_permissions). Then: no errors and B's first
    # name is updated.

    # given staff A (MANAGE_STAFF + MANAGE_ORDERS) and staff B (READ_ORDERS only)
    _give_unrestricted_group(
        staff_api_client.user, permission_manage_staff, permission_manage_orders
    )
    member = staff_users[1]
    _give_unrestricted_group(member, permission_read_orders)
    original_first_name = member.first_name
    new_first_name = "Changed"

    # when A updates B
    response = staff_api_client.post_graphql(
        STAFF_UPDATE_MUTATION,
        {
            "id": graphene.Node.to_global_id("User", member.pk),
            "input": {"firstName": new_first_name},
        },
    )

    # then (WRONG) B is considered out of A's scope and is left unchanged
    data = get_graphql_content(response)["data"]["staffUpdate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["code"] == AccountErrorCode.OUT_OF_SCOPE_USER.name
    assert data["errors"][0]["message"] == "You can't manage this user."
    member.refresh_from_db(fields=["first_name"])
    assert member.first_name == original_first_name


# --------------------------------------------------------------------------- #
# 3. MANAGE-gated read sites never widened with expand_read_permissions
# --------------------------------------------------------------------------- #
# Other sites with the same defect (not reproduced here): User.attributes /
# assignedAttribute (account/types.py), Order granted-refund / event `user`
# (order/types.py), hidden attributes in translatable content
# (translations/types.py), federation `User` refs (account/resolvers.py).
# SUGGESTED FIX for the whole family: wrap each site in expand_read_permissions
# and add a test that fails on any un-wrapped `has_perm(MANAGE_X)` with a twin
# under saleor/graphql/**/types.py and resolvers.py.

USER_ORDERS_QUERY = """
    query ($id: ID!, $where: CustomerOrderWhereInput) {
        user(id: $id) {
            orders(first: 10, where: $where) {
                edges { node { id } }
            }
        }
    }
"""


def test_read_orders_user_orders_hides_drafts_without_where(
    app_api_client,
    customer_user,
    order_generator,
    permission_read_users,
    permission_read_orders,
):
    # Scenario: User.orders has two code paths. With `where` (queryset path) the
    # draft filter is widened to READ_ORDERS; without `where` (dataloader path)
    # it still checks `requester.has_perm(MANAGE_ORDERS)` literally. A
    # READ_ORDERS holder therefore gets different rows for the same customer
    # depending on whether `where` is passed — drafts silently disappear.
    #
    # SUGGESTED OUTCOME: the dataloader path uses
    # has_one_of_permissions(expand_read_permissions([MANAGE_ORDERS])). Then:
    # both queries return {draft, order}.

    # given an app with READ_USERS + READ_ORDERS and a customer with a regular
    # and a draft order
    app_api_client.app.permissions.add(permission_read_users, permission_read_orders)
    order = order_generator()
    draft = order_generator(status=OrderStatus.DRAFT)
    order_id = graphene.Node.to_global_id("Order", order.pk)
    draft_id = graphene.Node.to_global_id("Order", draft.pk)
    user_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when querying the customer's orders without and with `where`
    without_where = get_graphql_content(
        app_api_client.post_graphql(USER_ORDERS_QUERY, {"id": user_id})
    )
    with_where = get_graphql_content(
        app_api_client.post_graphql(
            USER_ORDERS_QUERY,
            {"id": user_id, "where": {"ids": [order_id, draft_id]}},
        )
    )

    # then (WRONG) the draft is only visible when `where` is passed
    edges_without = without_where["data"]["user"]["orders"]["edges"]
    edges_with = with_where["data"]["user"]["orders"]["edges"]
    assert {edge["node"]["id"] for edge in edges_without} == {order_id}
    assert {edge["node"]["id"] for edge in edges_with} == {order_id, draft_id}


ADDRESS_QUERY = """
    query ($id: ID!) {
        address(id: $id) { id }
    }
"""


def test_read_users_app_cannot_read_address(
    app_api_client, customer_user, permission_read_users
):
    # Scenario: resolve_address lets an app through only with a literal
    # `app.has_perm(MANAGE_USERS)`. An app with READ_USERS can read the customer
    # (including addresses via User.addresses) but `address(id)` is denied.
    #
    # SUGGESTED OUTCOME: resolve_address / resolve_addresses (federation) use
    # has_one_of_permissions(app, expand_read_permissions([MANAGE_USERS])).
    # Then: the address is returned with the queried id.

    # given an app holding only READ_USERS and a customer's address
    app_api_client.app.permissions.add(permission_read_users)
    address = customer_user.default_billing_address
    variables = {"id": graphene.Node.to_global_id("Address", address.pk)}

    # when the app looks up the address by ID
    response = app_api_client.post_graphql(ADDRESS_QUERY, variables)

    # then (WRONG) it is denied
    assert_no_permission(response)


CUSTOMER_EVENTS_QUERY = """
    query ($id: ID!) {
        user(id: $id) {
            events { id user { id } }
        }
    }
"""


def test_read_users_cannot_read_customer_event_user(
    staff_api_client, customer_user, permission_read_users
):
    # Scenario: User.events is widened to READ_USERS, but CustomerEvent.user
    # still checks `has_perm(MANAGE_USERS) or has_perm(MANAGE_STAFF)` literally.
    # A READ_USERS holder sees the event list but every `user` sub-field raises
    # PermissionDenied.
    #
    # SUGGESTED OUTCOME: CustomerEvent.resolve_user uses
    # has_one_of_permissions(user, expand_read_permissions([MANAGE_STAFF,
    # MANAGE_USERS])). Then: no errors and `events[0].user.id` is the customer.

    # given a staff user holding only READ_USERS and a customer event
    staff_api_client.user.user_permissions.add(permission_read_users)
    event = CustomerEvent.objects.create(
        user=customer_user, type=CustomerEvents.NOTE_ADDED
    )
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when reading the event's user
    response = staff_api_client.post_graphql(CUSTOMER_EVENTS_QUERY, variables)

    # then (WRONG) the events are listed but their `user` is denied
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["extensions"]["exception"]["code"] == (
        "PermissionDenied"
    )
    assert content["data"]["user"]["events"] == [
        {"id": graphene.Node.to_global_id("CustomerEvent", event.pk), "user": None}
    ]


# --------------------------------------------------------------------------- #
# 4. Webhook subscriber lookup matches the exact MANAGE_X codename only
# --------------------------------------------------------------------------- #


def test_read_orders_app_does_not_receive_order_webhooks(
    app, webhook, permission_read_orders
):
    # Scenario: a typical read-only integration holds READ_ORDERS and subscribes
    # to ORDER_CREATED. get_filter_for_single_webhook_event filters apps by the
    # exact MANAGE_ORDERS codename, so the webhook is never selected and never
    # delivered. webhookDryRun / webhookTrigger / sample payload resolvers deny
    # it the same way.
    #
    # SUGGESTED OUTCOME: filter with `permissions__codename__in=[manage,
    # read_twin]` and use has_one_of_permissions(expand_read_permissions([...]))
    # in the resolver/mutation checks — or record the exclusion in the ADR.
    # Then: the READ_ORDERS app's webhook is returned.

    # given an active app holding only READ_ORDERS with an ORDER_CREATED webhook
    app.permissions.set([permission_read_orders])
    assert webhook.events.filter(
        event_type=WebhookEventAsyncType.ORDER_CREATED
    ).exists()
    assert app.has_perm("order.manage_orders") is False

    # when looking up subscribers for ORDER_CREATED
    webhooks = get_webhooks_for_event(WebhookEventAsyncType.ORDER_CREATED)

    # then (WRONG) the read-only app's webhook is not selected
    assert list(webhooks) == []
