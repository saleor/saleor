import graphene

from .....payment.models import TransactionItem
from .....payment.utils import payment_owned_by_user
from ....tests.utils import assert_no_permission
from . import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY
from .test_delete_private_metadata import (
    execute_clear_private_metadata_for_item,
    item_without_private_metadata,
)
from .test_update_metadata import (
    UPDATE_PUBLIC_METADATA_MUTATION,
    execute_update_public_metadata_for_item,
    item_contains_proper_public_metadata,
)
from .test_update_private_metadata import (
    UPDATE_PRIVATE_METADATA_MUTATION,
    execute_update_private_metadata_for_item,
    item_contains_proper_private_metadata,
)


def test_update_private_metadata_for_payment_by_staff(
    staff_api_client, permission_manage_payments, payment_with_private_metadata
):
    # given
    payment_id = graphene.Node.to_global_id("Payment", payment_with_private_metadata.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_payments,
        payment_id,
        "Payment",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        payment_with_private_metadata,
        payment_id,
        value="NewMetaValue",
    )


def test_update_private_metadata_for_payment_by_app(
    app_api_client, permission_manage_payments, payment_with_private_metadata
):
    # given
    payment_id = graphene.Node.to_global_id("Payment", payment_with_private_metadata.pk)

    # when
    response = execute_update_private_metadata_for_item(
        app_api_client,
        permission_manage_payments,
        payment_id,
        "Payment",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        payment_with_private_metadata,
        payment_id,
        value="NewMetaValue",
    )


def test_update_private_metadata_for_payment_by_staff_without_permission(
    staff_api_client, payment_with_private_metadata
):
    # given
    payment_id = graphene.Node.to_global_id("Payment", payment_with_private_metadata.pk)
    variables = {
        "id": payment_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Payment", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_payment_by_app_without_permission(
    app_api_client, payment
):
    # given
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {
        "id": payment_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = app_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Payment", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_delete_private_metadata_for_transaction_item(
    staff_api_client, permission_manage_payments, voucher
):
    # given
    transaction_item = TransactionItem.objects.create(
        private_metadata={PRIVATE_KEY: PRIVATE_VALUE}
    )
    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_payments, transaction_id, "TransactionItem"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        transaction_item,
        transaction_id,
    )


def test_update_public_metadata_for_payment_by_logged_user(
    user_api_client, payment_with_public_metadata
):
    # given
    payment_with_public_metadata.order.user = user_api_client.user
    payment_with_public_metadata.order.save()
    payment_id = graphene.Node.to_global_id("Payment", payment_with_public_metadata.pk)

    # when
    response = execute_update_public_metadata_for_item(
        user_api_client, None, payment_id, "Payment", value="NewMetaValue"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        payment_with_public_metadata,
        payment_id,
        value="NewMetaValue",
    )


def test_update_public_metadata_for_payment_by_different_logged_user(
    user2_api_client, payment_with_public_metadata
):
    # given
    assert not payment_owned_by_user(
        payment_with_public_metadata.pk, user2_api_client.user
    )
    payment_id = graphene.Node.to_global_id("Payment", payment_with_public_metadata.pk)
    variables = {
        "id": payment_id,
        "input": [{"key": PUBLIC_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = user2_api_client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % "Payment", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_public_metadata_for_payment_by_non_logged_user(
    api_client, payment_with_public_metadata
):
    # given
    payment_id = graphene.Node.to_global_id("Payment", payment_with_public_metadata.pk)
    variables = {
        "id": payment_id,
        "input": [{"key": PUBLIC_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = api_client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % "Payment", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_add_private_metadata_for_transaction_item(
    staff_api_client, permission_manage_payments
):
    # given
    transaction_item = TransactionItem.objects.create(
        private_metadata={PRIVATE_KEY: PRIVATE_VALUE}
    )
    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_payments, transaction_id, "TransactionItem"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        transaction_item,
        transaction_id,
    )
