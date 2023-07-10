import graphene

from ....tests.utils import get_graphql_content

MUTATION_STAFF_NOTIFICATION_RECIPIENT_CREATE = """
    mutation StaffNotificationRecipient ($input: StaffNotificationRecipientInput!) {
        staffNotificationRecipientCreate(input: $input) {
            staffNotificationRecipient {
                active
                email
                user {
                    id
                    firstName
                    lastName
                    email
                }
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


def test_staff_notification_create_mutation(
    staff_api_client, staff_user, permission_manage_settings
):
    # given
    user_id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"input": {"user": user_id}}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_STAFF_NOTIFICATION_RECIPIENT_CREATE,
        variables,
        permissions=[permission_manage_settings],
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["staffNotificationRecipientCreate"] == {
        "staffNotificationRecipient": {
            "active": True,
            "email": staff_user.email,
            "user": {
                "id": user_id,
                "firstName": staff_user.first_name,
                "lastName": staff_user.last_name,
                "email": staff_user.email,
            },
        },
        "errors": [],
    }


def test_staff_notification_create_mutation_with_staffs_email(
    staff_api_client, staff_user, permission_manage_settings
):
    # given
    user_id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"input": {"email": staff_user.email}}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_STAFF_NOTIFICATION_RECIPIENT_CREATE,
        variables,
        permissions=[permission_manage_settings],
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["staffNotificationRecipientCreate"] == {
        "staffNotificationRecipient": {
            "active": True,
            "email": staff_user.email,
            "user": {
                "id": user_id,
                "firstName": staff_user.first_name,
                "lastName": staff_user.last_name,
                "email": staff_user.email,
            },
        },
        "errors": [],
    }


def test_staff_notification_create_mutation_with_customer_user(
    staff_api_client, customer_user, permission_manage_settings
):
    # given
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"input": {"user": user_id}}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_STAFF_NOTIFICATION_RECIPIENT_CREATE,
        variables,
        permissions=[permission_manage_settings],
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["staffNotificationRecipientCreate"] == {
        "staffNotificationRecipient": None,
        "errors": [
            {"code": "INVALID", "field": "user", "message": "User has to be staff user"}
        ],
    }


def test_staff_notification_create_mutation_with_email(
    staff_api_client, permission_manage_settings, permission_manage_staff
):
    # given
    staff_email = "test_email@example.com"
    variables = {"input": {"email": staff_email}}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_STAFF_NOTIFICATION_RECIPIENT_CREATE,
        variables,
        permissions=[permission_manage_settings, permission_manage_staff],
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["staffNotificationRecipientCreate"] == {
        "staffNotificationRecipient": {
            "active": True,
            "email": staff_email,
            "user": None,
        },
        "errors": [],
    }


def test_staff_notification_create_mutation_with_empty_email(
    staff_api_client, permission_manage_settings
):
    # given
    staff_email = ""
    variables = {"input": {"email": staff_email}}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_STAFF_NOTIFICATION_RECIPIENT_CREATE,
        variables,
        permissions=[permission_manage_settings],
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["staffNotificationRecipientCreate"] == {
        "staffNotificationRecipient": None,
        "errors": [
            {
                "code": "INVALID",
                "field": "staffNotification",
                "message": "User and email cannot be set empty",
            }
        ],
    }
