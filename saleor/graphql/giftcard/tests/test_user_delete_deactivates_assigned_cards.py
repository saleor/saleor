import graphene

from ....account.models import User
from ....core.tokens import account_delete_token_generator
from ....giftcard import GiftCardEvents
from ....giftcard.models import GiftCardEvent
from ...tests.utils import get_graphql_content

CUSTOMER_DELETE = """
    mutation CustomerDelete($id: ID!) {
        customerDelete(id: $id) {
            errors { field message }
            user { id }
        }
    }
"""

ACCOUNT_DELETE = """
    mutation AccountDelete($token: String!) {
        accountDelete(token: $token) {
            errors { field message }
        }
    }
"""

STAFF_DELETE = """
    mutation StaffDelete($id: ID!) {
        staffDelete(id: $id) {
            errors { field message }
        }
    }
"""

CUSTOMER_BULK_DELETE = """
    mutation customerBulkDelete($ids: [ID!]!) {
        customerBulkDelete(ids: $ids) { count }
    }
"""

STAFF_BULK_DELETE = """
    mutation staffBulkDelete($ids: [ID!]!) {
        staffBulkDelete(ids: $ids) { count }
    }
"""


def _assign(gift_card, user):
    gift_card.assigned_to = user
    gift_card.assigned_to_email = user.email
    gift_card.is_active = True
    gift_card.save(update_fields=["assigned_to", "assigned_to_email", "is_active"])


def _assert_detached_and_deactivated(gift_card, assigned_email):
    gift_card.refresh_from_db()
    # assigned_to is nulled (otherwise on_delete=PROTECT would block the delete),
    # the card is deactivated and the assignee email is retained.
    assert gift_card.assigned_to_id is None
    assert gift_card.is_active is False
    assert gift_card.assigned_to_email == assigned_email
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.DEACTIVATED
    ).exists()


def test_customer_delete_deactivates_assigned_gift_card(
    staff_api_client, customer_user, gift_card, permission_manage_users
):
    # given
    _assign(gift_card, customer_user)
    assigned_email = customer_user.email
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_DELETE, variables, permissions=[permission_manage_users]
    )

    # then
    data = get_graphql_content(response)["data"]["customerDelete"]
    assert data["errors"] == []
    assert not User.objects.filter(pk=customer_user.pk).exists()
    _assert_detached_and_deactivated(gift_card, assigned_email)


def test_account_delete_deactivates_assigned_gift_card(user_api_client, gift_card):
    # given
    user = user_api_client.user
    _assign(gift_card, user)
    assigned_email = user.email
    token = account_delete_token_generator.make_token(user)

    # when
    response = user_api_client.post_graphql(ACCOUNT_DELETE, {"token": token})

    # then
    data = get_graphql_content(response)["data"]["accountDelete"]
    assert data["errors"] == []
    assert not User.objects.filter(pk=user.pk).exists()
    _assert_detached_and_deactivated(gift_card, assigned_email)


def test_staff_delete_deactivates_assigned_gift_card(
    staff_api_client, gift_card, permission_manage_staff
):
    # given
    staff = User.objects.create(email="to-delete@example.com", is_staff=True)
    _assign(gift_card, staff)
    assigned_email = staff.email
    variables = {"id": graphene.Node.to_global_id("User", staff.pk)}

    # when
    response = staff_api_client.post_graphql(
        STAFF_DELETE, variables, permissions=[permission_manage_staff]
    )

    # then
    data = get_graphql_content(response)["data"]["staffDelete"]
    assert data["errors"] == []
    assert not User.objects.filter(pk=staff.pk).exists()
    _assert_detached_and_deactivated(gift_card, assigned_email)


def test_customer_bulk_delete_deactivates_assigned_gift_card(
    staff_api_client, customer_user, gift_card, permission_manage_users
):
    # given
    _assign(gift_card, customer_user)
    assigned_email = customer_user.email
    variables = {"ids": [graphene.Node.to_global_id("User", customer_user.pk)]}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_BULK_DELETE, variables, permissions=[permission_manage_users]
    )

    # then
    assert get_graphql_content(response)["data"]["customerBulkDelete"]["count"] == 1
    assert not User.objects.filter(pk=customer_user.pk).exists()
    _assert_detached_and_deactivated(gift_card, assigned_email)


def test_staff_bulk_delete_deactivates_assigned_gift_card(
    staff_api_client, gift_card, permission_manage_staff
):
    # given
    staff = User.objects.create(email="to-delete@example.com", is_staff=True)
    _assign(gift_card, staff)
    assigned_email = staff.email
    variables = {"ids": [graphene.Node.to_global_id("User", staff.pk)]}

    # when
    response = staff_api_client.post_graphql(
        STAFF_BULK_DELETE, variables, permissions=[permission_manage_staff]
    )

    # then
    assert get_graphql_content(response)["data"]["staffBulkDelete"]["count"] == 1
    assert not User.objects.filter(pk=staff.pk).exists()
    _assert_detached_and_deactivated(gift_card, assigned_email)
