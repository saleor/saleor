import graphene
import pytest
from django.core.exceptions import ValidationError

from .....account.models import User
from .....order.error_codes import OrderBulkCreateErrorCode
from ...bulk_mutations.utils import get_instance

USER_KEY_MAP = {
    "user_id": "id",
    "user_email": "email",
}


def test_get_instance(customer_user):
    input = {
        "user_id": graphene.Node.to_global_id("User", customer_user.id),
        "dummy_data": ["abc", 1],
    }
    object_storage = {f"User.id.{customer_user.id}": customer_user}
    assert (
        get_instance(
            input, User, USER_KEY_MAP, object_storage, OrderBulkCreateErrorCode
        )
        == customer_user
    )


def test_get_instance_fail_multiple_identifiers(customer_user):
    input = {
        "user_id": graphene.Node.to_global_id("User", customer_user.id),
        "user_email": customer_user.email,
    }
    with pytest.raises(ValidationError) as error:
        get_instance(input, User, USER_KEY_MAP, {}, OrderBulkCreateErrorCode)

    assert (
        error.value.message == "Only one of [user_id, user_email] arguments can"
        " be provided to resolve User instance."
    )


def test_get_instance_fail_no_identifier(customer_user):
    input = {"dummy_data": ["abc", 1]}
    with pytest.raises(ValidationError) as error:
        get_instance(input, User, USER_KEY_MAP, {}, OrderBulkCreateErrorCode)

    assert (
        error.value.message == "One of [user_id, user_email] arguments must"
        " be provided to resolve User instance."
    )


def test_get_instance_fail_invalid_global_id_syntax(customer_user):
    input = {"user_id": "wrong_global_ID"}
    with pytest.raises(ValidationError) as error:
        get_instance(input, User, USER_KEY_MAP, {}, OrderBulkCreateErrorCode)

    assert error.value.message == "Invalid ID: wrong_global_ID. Expected: User."


def test_get_instance_fail_invalid_global_id_model(customer_user, app):
    app_global_id = graphene.Node.to_global_id("App", app.id)
    input = {"user_id": app_global_id}
    with pytest.raises(ValidationError) as error:
        get_instance(input, User, USER_KEY_MAP, {}, OrderBulkCreateErrorCode)

    assert (
        error.value.message
        == f"Invalid ID: {app_global_id}. Expected: User, received: App."
    )


def test_get_instance_fail_non_existing_global_id(customer_user):
    non_existing_email = "non_existing@example.com"
    input = {"user_email": non_existing_email}
    with pytest.raises(ValidationError) as error:
        get_instance(input, User, USER_KEY_MAP, {}, OrderBulkCreateErrorCode)

    assert (
        error.value.message == "User instance with email=non_existing@example.com"
        " doesn't exist."
    )
