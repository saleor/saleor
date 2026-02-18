from decimal import Decimal
from unittest.mock import patch

import graphene

from .....page.models import Page, PageType
from .....payment import TransactionEventType
from .....payment.models import TransactionEvent
from .....webhook.event_types import WebhookEventSyncType
from ....core.enums import TransactionRequestActionErrorCode
from ....core.utils import to_global_id_or_none
from ....tests.utils import (
    get_graphql_content,
)
from ...enums import TransactionActionEnum

MUTATION_TRANSACTION_REQUEST_ACTION = """
mutation TransactionRequestAction(
    $id: ID
    $action_type: TransactionActionEnum!
    $amount: PositiveDecimal
    $refund_reason: String
    $refund_reason_reference: ID
    ){
    transactionRequestAction(
            id: $id,
            actionType: $action_type,
            amount: $amount,
            refundReason: $refund_reason,
            refundReasonReference: $refund_reason_reference
        ){
        transaction{
                id
                actions
                pspReference
                modifiedAt
                createdAt
                authorizedAmount{
                    amount
                    currency
                }
                chargedAmount{
                    currency
                    amount
                }
                refundedAmount{
                    currency
                    amount
                }
        }
        errors{
            field
            message
            code
        }
    }
}
"""

MUTATION_TRANSACTION_REQUEST_ACTION_BY_TOKEN = """
mutation TransactionRequestAction(
    $token: UUID
    $action_type: TransactionActionEnum!
    $amount: PositiveDecimal
    $reason: String
    $reason_reference: ID
    ){
    transactionRequestAction(
            token: $token,
            actionType: $action_type,
            amount: $amount,
            refundReason: $reason,
            refundReasonReference: $reason_reference
        ){
        transaction{
                id
                actions
                pspReference
                modifiedAt
                createdAt
                authorizedAmount{
                    amount
                    currency
                }
                chargedAmount{
                    currency
                    amount
                }
                refundedAmount{
                    currency
                    amount
                }
        }
        errors{
            field
            message
            code
        }
    }
}
"""


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_refund_with_reason_reference_required_created_by_user(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    staff_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
    permission_group_handle_payments,
    site_settings,
):
    # Given
    mocked_is_active.return_value = False

    # Create page type and page for refund reasons
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )

    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
        app=transaction_request_webhook.app,
    )

    page_id = to_global_id_or_none(page)
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "refund_reason": "Product was damaged during shipping",
        "refund_reason_reference": page_id,
    }
    staff_api_client.user.groups.add(permission_group_handle_payments)

    # When
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # Then
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestAction"]
    errors = data["errors"]
    assert not errors

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()

    assert request_event
    assert request_event.user == staff_api_client.user
    assert request_event.message == "Product was damaged during shipping"
    assert request_event.reason_reference == page


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_refund_with_reason_reference_required_but_not_provided_created_by_user(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    staff_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
    permission_group_handle_payments,
    site_settings,
):
    # Given
    mocked_is_active.return_value = False

    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
        app=transaction_request_webhook.app,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "refund_reason": "Product was damaged during shipping",
    }
    staff_api_client.user.groups.add(permission_group_handle_payments)

    # When
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # Then
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestAction"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "refundReasonReference"
    assert error["code"] == TransactionRequestActionErrorCode.REQUIRED.name

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()
    assert request_event is None


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_refund_with_reason_reference_required_but_not_provided_created_by_app(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    app_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
    site_settings,
):
    # Given
    mocked_is_active.return_value = False

    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
        app=transaction_request_webhook.app,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "refund_reason": "Product was damaged during shipping",
    }
    app_api_client.app.permissions.add(permission_manage_payments)

    # When
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # Then
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestAction"]
    errors = data["errors"]
    assert not errors

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()

    assert request_event
    assert request_event.app == app_api_client.app
    assert request_event.message == "Product was damaged during shipping"
    assert request_event.reason_reference is None


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_refund_with_reason_reference_not_configured_created_by_app(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    app_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
    site_settings,
):
    # Given
    mocked_is_active.return_value = False

    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )

    assert site_settings.refund_reason_reference_type is None

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
        app=transaction_request_webhook.app,
    )

    page_id = to_global_id_or_none(page)
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "refund_reason": "Product was damaged during shipping",
        "refund_reason_reference": page_id,  # Provided but should be ignored
    }
    app_api_client.app.permissions.add(permission_manage_payments)

    # When
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # Then
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestAction"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "refundReasonReference"
    assert error["code"] == TransactionRequestActionErrorCode.INVALID.name


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_refund_with_reason_reference_required_created_by_user_throws_for_invalid_id(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    staff_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
    permission_group_handle_payments,
    site_settings,
):
    # Given
    mocked_is_active.return_value = False

    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
        app=transaction_request_webhook.app,
    )

    invalid_page_id = graphene.Node.to_global_id("Page", 99999)

    assert Page.objects.count() == 0

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "refund_reason": "Product was damaged during shipping",
        "refund_reason_reference": invalid_page_id,
    }
    staff_api_client.user.groups.add(permission_group_handle_payments)

    # When
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # Then
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestAction"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "refundReasonReference"
    assert error["code"] == TransactionRequestActionErrorCode.INVALID.name

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()
    assert request_event is None


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_refund_with_reason_only_no_reference(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    staff_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
    permission_group_handle_payments,
    site_settings,
):
    # Given
    mocked_is_active.return_value = False

    assert site_settings.refund_reason_reference_type is None

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
        app=transaction_request_webhook.app,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "refund_reason": "Product was damaged during shipping",
    }
    staff_api_client.user.groups.add(permission_group_handle_payments)

    # When
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # Then
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestAction"]
    errors = data["errors"]
    assert not errors

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()

    assert request_event
    assert request_event.user == staff_api_client.user
    assert request_event.message == "Product was damaged during shipping"
    assert request_event.reason_reference is None


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_transaction_request_charge_rejects_reason_and_reference(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    staff_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
    permission_group_handle_payments,
    site_settings,
):
    # Given
    mocked_is_active.return_value = False

    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )

    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        authorized_value=Decimal(10),
        app=transaction_request_webhook.app,
    )

    page_id = to_global_id_or_none(page)
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CHARGE.name,
        "refund_reason": "Some reason that should be rejected",
        "refund_reason_reference": page_id,
    }
    staff_api_client.user.groups.add(permission_group_handle_payments)

    # When
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # Then
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestAction"]
    errors = data["errors"]
    assert len(errors) == 2

    # Check that both refund_reason and refund_reason_reference errors are present
    error_fields = [error["field"] for error in errors]
    assert "refundReason" in error_fields
    assert "refundReasonReference" in error_fields

    # Check error codes
    for error in errors:
        assert error["code"] == TransactionRequestActionErrorCode.INVALID.name

    # Check error messages
    reason_error = next(error for error in errors if error["field"] == "refundReason")
    reference_error = next(
        error for error in errors if error["field"] == "refundReasonReference"
    )

    assert "Reason can be set only for REFUND action" in reason_error["message"]
    assert (
        "Reason reference can be set only for REFUND action"
        in reference_error["message"]
    )

    # No transaction event should be created since validation failed
    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_REQUEST,
    ).first()
    assert request_event is None

    # Payment action should not be called
    assert not mocked_payment_action_request.called


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_refund_with_reason_reference_wrong_page_type_created_by_user(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    staff_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
    permission_group_handle_payments,
    site_settings,
):
    # Given
    mocked_is_active.return_value = False

    page_type1 = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type1
    site_settings.save()

    page_type2 = PageType.objects.create(name="Different Type", slug="different-type")
    page_wrong_type = Page.objects.create(
        slug="wrong-type-page",
        title="Wrong Type Page",
        page_type=page_type2,
        is_published=True,
    )

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
        app=transaction_request_webhook.app,
    )

    wrong_page_id = to_global_id_or_none(page_wrong_type)
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "refund_reason": "Product was damaged during shipping",
        "refund_reason_reference": wrong_page_id,
    }
    staff_api_client.user.groups.add(permission_group_handle_payments)

    # When
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # Then
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestAction"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "refundReasonReference"
    assert error["code"] == TransactionRequestActionErrorCode.INVALID.name

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()
    assert request_event is None


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_refund_with_reason_reference_not_valid_page_id(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    staff_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
    permission_group_handle_payments,
    site_settings,
):
    # Given
    mocked_is_active.return_value = False

    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
        app=transaction_request_webhook.app,
    )

    invalid_page_id = graphene.Node.to_global_id("Product", 12345)

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "refund_reason": "Product was damaged during shipping",
        "refund_reason_reference": invalid_page_id,
    }
    staff_api_client.user.groups.add(permission_group_handle_payments)

    # When
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # Then
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestAction"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == "GRAPHQL_ERROR"
    assert "Invalid ID:" in error["message"]
    assert "Expected: Page, received: Product" in error["message"]

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()
    assert request_event is None


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_refund_with_reason_reference_not_valid_id_format(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    staff_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
    permission_group_handle_payments,
    site_settings,
):
    # Given
    mocked_is_active.return_value = False

    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
        app=transaction_request_webhook.app,
    )

    invalid_id = "invalid-id-format"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "refund_reason": "Product was damaged during shipping",
        "refund_reason_reference": invalid_id,
    }
    staff_api_client.user.groups.add(permission_group_handle_payments)

    # When
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # Then
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestAction"]
    errors = data["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "reasonReference"
    assert error["code"] == "GRAPHQL_ERROR"
    assert "Invalid ID: invalid-id-format. Expected: Page." in error["message"]

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()
    assert request_event is None


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_transaction_request_charge_without_reason_when_refund_reasons_enabled(
    mocked_payment_action_request,
    mocked_is_active,
    order_with_lines,
    staff_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
    permission_group_handle_payments,
    site_settings,
):
    # Given
    mocked_is_active.return_value = False

    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save(update_fields=["refund_reason_reference_type"])

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED
    )

    authorization_amount = Decimal("10.00")
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        authorized_value=authorization_amount,
        app=transaction_request_webhook.app,
    )

    transaction.events.create(
        amount_value=authorization_amount,
        currency=transaction.currency,
        type=TransactionEventType.AUTHORIZATION_SUCCESS,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CHARGE.name,
        "amount": authorization_amount,
    }
    staff_api_client.user.groups.add(permission_group_handle_payments)

    # When
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # Then
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestAction"]
    errors = data["errors"]
    assert not errors, f"Expected no errors but got: {errors}"

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_REQUEST,
    ).first()

    assert request_event
    assert request_event.amount_value == authorization_amount
    assert request_event.user == staff_api_client.user
    assert request_event.message is None
    assert request_event.reason_reference is None

    assert mocked_payment_action_request.called
