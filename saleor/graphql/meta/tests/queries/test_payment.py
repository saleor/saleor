from typing import List

from .....payment.models import Payment
from .....payment.utils import payment_owned_by_user
from .....permission.models import Permission
from ....tests.fixtures import ApiClient
from ....tests.utils import assert_no_permission
from .utils import (
    assert_model_contains_metadata,
    assert_model_contains_private_metadata,
    execute_query,
)

QUERY_PAYMENT_PRIVATE_META = """
    query paymentsMeta($id: ID!){
        payment(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def execute_query_private_metadata_for_payment(
    client: ApiClient, payment: Payment, permissions: List[Permission] = None
):
    return execute_query(
        QUERY_PAYMENT_PRIVATE_META, client, payment, "Payment", permissions
    )


def assert_payment_contains_private_metadata(response):
    assert_model_contains_private_metadata(response, "payment")


def test_query_private_meta_for_payment_as_staff_with_permission(
    staff_api_client,
    payment_with_private_metadata,
    permission_manage_orders,
    permission_manage_payments,
):
    # when
    response = execute_query_private_metadata_for_payment(
        staff_api_client,
        payment_with_private_metadata,
        permissions=[permission_manage_orders, permission_manage_payments],
    )

    # then
    assert_payment_contains_private_metadata(response)


def test_query_private_meta_for_payment_as_staff_without_permission(
    staff_api_client, payment_with_private_metadata
):
    # when
    response = execute_query_private_metadata_for_payment(
        staff_api_client, payment_with_private_metadata
    )

    # then
    assert_no_permission(response)


def test_query_private_meta_for_payment_as_app_with_permission(
    app_api_client,
    payment_with_private_metadata,
    permission_manage_orders,
    permission_manage_payments,
):
    # when
    response = execute_query_private_metadata_for_payment(
        app_api_client,
        payment_with_private_metadata,
        permissions=[permission_manage_orders, permission_manage_payments],
    )

    # then
    assert_payment_contains_private_metadata(response)


def test_query_private_meta_for_payment_as_app_without_permission(
    app_api_client, payment_with_private_metadata
):
    # when
    response = execute_query_private_metadata_for_payment(
        app_api_client, payment_with_private_metadata
    )

    # then
    assert_no_permission(response)


QUERY_PAYMENT_PUBLIC_META = """
    query paymentsMeta($id: ID!){
        payment(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def execute_query_public_metadata_for_payment(
    client: ApiClient, payment: Payment, permissions: List[Permission] = None
):
    return execute_query(
        QUERY_PAYMENT_PUBLIC_META, client, payment, "Payment", permissions
    )


def assert_payment_contains_metadata(response):
    assert_model_contains_metadata(response, "payment")


def test_query_public_meta_for_payment_as_customer(
    user_api_client, payment_with_public_metadata, permission_manage_orders
):
    # given
    assert payment_owned_by_user(payment_with_public_metadata.pk, user_api_client.user)

    # when
    response = execute_query_public_metadata_for_payment(
        user_api_client,
        payment_with_public_metadata,
        permissions=[permission_manage_orders],
    )

    # then
    assert_payment_contains_metadata(response)


def test_query_public_meta_for_payment_as_another_customer(
    user2_api_client,
    payment_with_public_metadata,
    permission_manage_orders,
):
    # given
    assert not payment_owned_by_user(
        payment_with_public_metadata.pk, user2_api_client.user
    )
    # when
    response = execute_query_public_metadata_for_payment(
        user2_api_client,
        payment_with_public_metadata,
        permissions=[permission_manage_orders],
    )

    # then
    assert_no_permission(response)


def test_query_public_meta_for_payment_as_staff_with_permission(
    staff_api_client,
    payment_with_public_metadata,
    permission_manage_orders,
    permission_manage_payments,
):
    # when
    response = execute_query_public_metadata_for_payment(
        staff_api_client,
        payment_with_public_metadata,
        permissions=[permission_manage_orders, permission_manage_payments],
    )

    # then
    assert_payment_contains_metadata(response)


def test_query_public_meta_for_payment_as_staff_without_permission(
    staff_api_client, payment_with_public_metadata
):
    # when
    response = execute_query_public_metadata_for_payment(
        staff_api_client, payment_with_public_metadata
    )

    # then
    assert_no_permission(response)


def test_query_public_meta_for_payment_as_app_with_permission(
    app_api_client,
    payment_with_public_metadata,
    permission_manage_orders,
    permission_manage_payments,
):
    # when
    response = execute_query_public_metadata_for_payment(
        app_api_client,
        payment_with_public_metadata,
        permissions=[permission_manage_orders, permission_manage_payments],
    )

    # then
    assert_payment_contains_metadata(response)


def test_query_public_meta_for_payment_as_app_without_permission(
    app_api_client, payment_with_public_metadata
):
    # when
    response = execute_query_public_metadata_for_payment(
        app_api_client, payment_with_public_metadata
    )

    # then
    assert_no_permission(response)
