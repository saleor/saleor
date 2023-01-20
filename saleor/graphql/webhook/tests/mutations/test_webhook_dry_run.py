import json
import uuid

import graphene
import pytest

from .....graphql.tests.utils import get_graphql_content
from .....webhook.error_codes import WebhookDryRunErrorCode
from .....webhook.event_types import WebhookEventAsyncType
from ....tests.utils import assert_no_permission
from ...subscription_types import WEBHOOK_TYPES_MAP

WEBHOOK_DRY_RUN_MUTATION = """
    mutation webhookDryRun($query: String!, $objectId: ID!) {
        webhookDryRun(query: $query, objectId: $objectId) {
            errors {
                field
                code
                message
            }
            payload
        }
    }
    """


def test_webhook_dry_run(
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook

    variables = {"objectId": order_id, "query": webhook.subscription_query}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["webhookDryRun"]
    payload = json.loads(data["payload"])
    assert payload["order"]["id"] == order_id


def test_webhook_dry_run_missing_user_permission(
    staff_api_client,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook

    variables = {"objectId": order_id, "query": webhook.subscription_query}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert not error["field"]
    assert error["code"] == WebhookDryRunErrorCode.MISSING_PERMISSION.name
    assert (
        error["message"] == "The user doesn't have required permission: manage_orders."
    )


def test_webhook_dry_run_staff_user_not_authorized(
    user_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    user_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook

    variables = {"objectId": order_id, "query": webhook.subscription_query}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_webhook_dry_run_non_existing_id(
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", uuid.uuid4())
    webhook = subscription_order_created_webhook

    variables = {"objectId": order_id, "query": webhook.subscription_query}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert error["field"] == "objectId"
    assert error["code"] == WebhookDryRunErrorCode.NOT_FOUND.name
    assert error["message"] == f"Couldn't resolve to a node: {order_id}"


def test_webhook_dry_run_invalid_query(
    staff_api_client,
    permission_manage_orders,
    order,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    order_id = graphene.Node.to_global_id("Order", order.id)
    webhook = subscription_order_created_webhook
    subscription = webhook.subscription_query.replace("OrderCreated", "UndefinedEvent")

    variables = {"objectId": order_id, "query": subscription}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert error["field"] == "query"
    assert error["code"] == WebhookDryRunErrorCode.GRAPHQL_ERROR.name
    assert 'Unknown type "UndefinedEvent"' in error["message"]


def test_webhook_dry_run_object_id_does_not_match_event(
    staff_api_client,
    permission_manage_orders,
    product,
    subscription_order_created_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    product_id = graphene.Node.to_global_id("Product", product.id)
    webhook = subscription_order_created_webhook

    variables = {"objectId": product_id, "query": webhook.subscription_query}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert error["field"] == "objectId"
    assert error["code"] == WebhookDryRunErrorCode.INVALID_ID.name
    assert error["message"] == "ObjectId doesn't match event type."


def test_webhook_dry_run_event_type_not_supported(
    staff_api_client,
    permission_manage_orders,
    product,
    subscription_payment_authorize_webhook,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    product_id = graphene.Node.to_global_id("Product", product.id)
    webhook = subscription_payment_authorize_webhook

    variables = {"objectId": product_id, "query": webhook.subscription_query}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["webhookDryRun"]["errors"][0]
    assert error["field"] == "query"
    assert error["code"] == WebhookDryRunErrorCode.TYPE_NOT_SUPPORTED.name
    assert error["message"] == "Event type: PaymentAuthorize not supported."


@pytest.fixture
def async_subscription_webhooks_with_root_objects(
    subscription_address_created_webhook,
    subscription_address_updated_webhook,
    subscription_address_deleted_webhook,
    subscription_app_installed_webhook,
    subscription_app_updated_webhook,
    subscription_app_deleted_webhook,
    subscription_app_status_changed_webhook,
    subscription_attribute_created_webhook,
    subscription_attribute_updated_webhook,
    subscription_attribute_deleted_webhook,
    subscription_attribute_value_created_webhook,
    subscription_attribute_value_updated_webhook,
    subscription_attribute_value_deleted_webhook,
    subscription_category_created_webhook,
    subscription_category_updated_webhook,
    subscription_category_deleted_webhook,
    subscription_channel_created_webhook,
    subscription_channel_updated_webhook,
    subscription_channel_deleted_webhook,
    subscription_channel_status_changed_webhook,
    subscription_gift_card_created_webhook,
    subscription_gift_card_updated_webhook,
    subscription_gift_card_deleted_webhook,
    subscription_gift_card_status_changed_webhook,
    subscription_gift_card_metadata_updated_webhook,
    subscription_menu_created_webhook,
    subscription_menu_updated_webhook,
    subscription_menu_deleted_webhook,
    subscription_menu_item_created_webhook,
    subscription_menu_item_updated_webhook,
    subscription_menu_item_deleted_webhook,
    subscription_shipping_price_created_webhook,
    subscription_shipping_price_updated_webhook,
    subscription_shipping_price_deleted_webhook,
    subscription_shipping_zone_created_webhook,
    subscription_shipping_zone_updated_webhook,
    subscription_shipping_zone_deleted_webhook,
    subscription_shipping_zone_metadata_updated_webhook,
    subscription_product_updated_webhook,
    subscription_product_created_webhook,
    subscription_product_deleted_webhook,
    subscription_product_metadata_updated_webhook,
    subscription_product_variant_created_webhook,
    subscription_product_variant_updated_webhook,
    subscription_product_variant_deleted_webhook,
    subscription_product_variant_metadata_updated_webhook,
    subscription_product_variant_out_of_stock_webhook,
    subscription_product_variant_back_in_stock_webhook,
    subscription_order_created_webhook,
    subscription_order_updated_webhook,
    subscription_order_confirmed_webhook,
    subscription_order_fully_paid_webhook,
    subscription_order_cancelled_webhook,
    subscription_order_fulfilled_webhook,
    subscription_order_metadata_updated_webhook,
    subscription_draft_order_created_webhook,
    subscription_draft_order_updated_webhook,
    subscription_draft_order_deleted_webhook,
    subscription_sale_created_webhook,
    subscription_sale_updated_webhook,
    subscription_sale_deleted_webhook,
    subscription_sale_toggle_webhook,
    subscription_invoice_requested_webhook,
    subscription_invoice_deleted_webhook,
    subscription_invoice_sent_webhook,
    subscription_fulfillment_created_webhook,
    subscription_fulfillment_canceled_webhook,
    subscription_fulfillment_approved_webhook,
    subscription_fulfillment_metadata_updated_webhook,
    subscription_customer_created_webhook,
    subscription_customer_updated_webhook,
    subscription_customer_deleted_webhook,
    subscription_customer_metadata_updated_webhook,
    subscription_collection_created_webhook,
    subscription_collection_updated_webhook,
    subscription_collection_deleted_webhook,
    subscription_collection_metadata_updated_webhook,
    subscription_checkout_created_webhook,
    subscription_checkout_updated_webhook,
    subscription_checkout_metadata_updated_webhook,
    subscription_page_created_webhook,
    subscription_page_updated_webhook,
    subscription_page_deleted_webhook,
    subscription_page_type_created_webhook,
    subscription_page_type_updated_webhook,
    subscription_page_type_deleted_webhook,
    subscription_permission_group_created_webhook,
    subscription_permission_group_updated_webhook,
    subscription_permission_group_deleted_webhook,
    subscription_product_created_multiple_events_webhook,
    subscription_staff_created_webhook,
    subscription_staff_updated_webhook,
    subscription_staff_deleted_webhook,
    subscription_transaction_item_metadata_updated_webhook,
    subscription_translation_created_webhook,
    subscription_translation_updated_webhook,
    subscription_warehouse_created_webhook,
    subscription_warehouse_updated_webhook,
    subscription_warehouse_deleted_webhook,
    subscription_warehouse_metadata_updated_webhook,
    subscription_voucher_created_webhook,
    subscription_voucher_updated_webhook,
    subscription_voucher_deleted_webhook,
    subscription_voucher_webhook_with_meta,
    subscription_voucher_metadata_updated_webhook,
    address,
    app,
    numeric_attribute,
    category,
    channel_PLN,
    gift_card,
    menu_item,
    shipping_method,
    product,
    fulfilled_order,
    sale,
    fulfillment,
    stock,
    customer_user,
    collection,
    checkout,
    page,
    permission_group_manage_users,
    shipping_zone,
    staff_user,
    voucher,
    warehouse,
    translated_attribute,
    transaction_item,
):
    events = WebhookEventAsyncType
    attr = numeric_attribute
    attr_value = attr.values.first()
    menu = menu_item.menu
    order = fulfilled_order
    invoice = order.invoices.first()
    page_type = page.page_type

    return {
        events.ADDRESS_UPDATED: [subscription_address_updated_webhook, address],
        events.ADDRESS_CREATED: [subscription_address_created_webhook, address],
        events.ADDRESS_DELETED: [subscription_address_deleted_webhook, address],
        events.APP_UPDATED: [subscription_app_updated_webhook, app],
        events.APP_DELETED: [subscription_app_deleted_webhook, app],
        events.APP_INSTALLED: [subscription_app_installed_webhook, app],
        events.APP_STATUS_CHANGED: [subscription_app_status_changed_webhook, app],
        events.ATTRIBUTE_CREATED: [subscription_attribute_created_webhook, attr],
        events.ATTRIBUTE_UPDATED: [subscription_attribute_updated_webhook, attr],
        events.ATTRIBUTE_DELETED: [subscription_attribute_deleted_webhook, attr],
        events.ATTRIBUTE_VALUE_UPDATED: [
            subscription_attribute_value_updated_webhook,
            attr_value,
        ],
        events.ATTRIBUTE_VALUE_CREATED: [
            subscription_attribute_value_created_webhook,
            attr_value,
        ],
        events.ATTRIBUTE_VALUE_DELETED: [
            subscription_attribute_value_deleted_webhook,
            attr_value,
        ],
        events.CATEGORY_CREATED: [subscription_category_created_webhook, category],
        events.CATEGORY_UPDATED: [subscription_category_updated_webhook, category],
        events.CATEGORY_DELETED: [subscription_category_deleted_webhook, category],
        events.CHANNEL_CREATED: [subscription_channel_created_webhook, channel_PLN],
        events.CHANNEL_UPDATED: [subscription_channel_updated_webhook, channel_PLN],
        events.CHANNEL_DELETED: [subscription_channel_deleted_webhook, channel_PLN],
        events.CHANNEL_STATUS_CHANGED: [
            subscription_channel_status_changed_webhook,
            channel_PLN,
        ],
        events.GIFT_CARD_CREATED: [subscription_gift_card_created_webhook, gift_card],
        events.GIFT_CARD_UPDATED: [subscription_gift_card_updated_webhook, gift_card],
        events.GIFT_CARD_DELETED: [subscription_gift_card_deleted_webhook, gift_card],
        events.GIFT_CARD_STATUS_CHANGED: [
            subscription_gift_card_status_changed_webhook,
            gift_card,
        ],
        events.GIFT_CARD_METADATA_UPDATED: [
            subscription_gift_card_metadata_updated_webhook,
            gift_card,
        ],
        events.MENU_CREATED: [subscription_menu_created_webhook, menu],
        events.MENU_UPDATED: [subscription_menu_updated_webhook, menu],
        events.MENU_DELETED: [subscription_menu_deleted_webhook, menu],
        events.MENU_ITEM_CREATED: [subscription_menu_item_created_webhook, menu_item],
        events.MENU_ITEM_UPDATED: [subscription_menu_item_updated_webhook, menu_item],
        events.MENU_ITEM_DELETED: [subscription_menu_item_deleted_webhook, menu_item],
        events.ORDER_CREATED: [subscription_order_created_webhook, order],
        events.ORDER_UPDATED: [subscription_order_updated_webhook, order],
        events.ORDER_CONFIRMED: [subscription_order_confirmed_webhook, order],
        events.ORDER_FULLY_PAID: [subscription_order_fully_paid_webhook, order],
        events.ORDER_FULFILLED: [subscription_order_fulfilled_webhook, order],
        events.ORDER_CANCELLED: [subscription_order_cancelled_webhook, order],
        events.ORDER_METADATA_UPDATED: [
            subscription_order_metadata_updated_webhook,
            order,
        ],
        events.DRAFT_ORDER_CREATED: [subscription_draft_order_created_webhook, order],
        events.DRAFT_ORDER_UPDATED: [subscription_draft_order_updated_webhook, order],
        events.DRAFT_ORDER_DELETED: [subscription_draft_order_deleted_webhook, order],
        events.PRODUCT_CREATED: [subscription_product_created_webhook, product],
        events.PRODUCT_UPDATED: [subscription_product_updated_webhook, product],
        events.PRODUCT_DELETED: [subscription_product_deleted_webhook, product],
        events.PRODUCT_METADATA_UPDATED: [
            subscription_product_metadata_updated_webhook,
            product,
        ],
        events.PRODUCT_VARIANT_CREATED: [
            subscription_product_variant_created_webhook,
            product,
        ],
        events.PRODUCT_VARIANT_UPDATED: [
            subscription_product_variant_updated_webhook,
            product,
        ],
        events.PRODUCT_VARIANT_OUT_OF_STOCK: [
            subscription_product_variant_out_of_stock_webhook,
            stock,
        ],
        events.PRODUCT_VARIANT_BACK_IN_STOCK: [
            subscription_product_variant_back_in_stock_webhook,
            stock,
        ],
        events.PRODUCT_VARIANT_DELETED: [
            subscription_product_variant_deleted_webhook,
            product,
        ],
        events.PRODUCT_VARIANT_METADATA_UPDATED: [
            subscription_product_variant_metadata_updated_webhook,
            product,
        ],
        events.SALE_CREATED: [subscription_sale_created_webhook, sale],
        events.SALE_UPDATED: [subscription_sale_updated_webhook, sale],
        events.SALE_DELETED: [subscription_sale_deleted_webhook, sale],
        events.SALE_TOGGLE: [subscription_sale_toggle_webhook, sale],
        events.INVOICE_REQUESTED: [subscription_invoice_requested_webhook, invoice],
        events.INVOICE_DELETED: [subscription_invoice_deleted_webhook, invoice],
        events.INVOICE_SENT: [subscription_invoice_sent_webhook, invoice],
        events.FULFILLMENT_CREATED: [
            subscription_fulfillment_created_webhook,
            fulfillment,
        ],
        events.FULFILLMENT_CANCELED: [
            subscription_fulfillment_canceled_webhook,
            fulfillment,
        ],
        events.FULFILLMENT_APPROVED: [
            subscription_fulfillment_approved_webhook,
            fulfillment,
        ],
        events.FULFILLMENT_METADATA_UPDATED: [
            subscription_fulfillment_metadata_updated_webhook,
            fulfillment,
        ],
        events.CUSTOMER_CREATED: [subscription_customer_created_webhook, customer_user],
        events.CUSTOMER_UPDATED: [subscription_customer_updated_webhook, customer_user],
        events.CUSTOMER_METADATA_UPDATED: [
            subscription_customer_metadata_updated_webhook,
            customer_user,
        ],
        events.COLLECTION_CREATED: [
            subscription_collection_created_webhook,
            collection,
        ],
        events.COLLECTION_UPDATED: [
            subscription_collection_updated_webhook,
            collection,
        ],
        events.COLLECTION_DELETED: [
            subscription_collection_deleted_webhook,
            collection,
        ],
        events.COLLECTION_METADATA_UPDATED: [
            subscription_collection_metadata_updated_webhook,
            collection,
        ],
        events.CHECKOUT_CREATED: [subscription_checkout_created_webhook, checkout],
        events.CHECKOUT_UPDATED: [subscription_checkout_updated_webhook, checkout],
        events.CHECKOUT_METADATA_UPDATED: [
            subscription_checkout_metadata_updated_webhook,
            checkout,
        ],
        events.PAGE_CREATED: [subscription_page_created_webhook, page],
        events.PAGE_UPDATED: [subscription_page_updated_webhook, page],
        events.PAGE_DELETED: [subscription_page_deleted_webhook, page],
        events.PAGE_TYPE_CREATED: [subscription_page_type_created_webhook, page_type],
        events.PAGE_TYPE_UPDATED: [subscription_page_type_updated_webhook, page_type],
        events.PAGE_TYPE_DELETED: [subscription_page_type_deleted_webhook, page_type],
        events.PERMISSION_GROUP_CREATED: [
            subscription_permission_group_created_webhook,
            permission_group_manage_users,
        ],
        events.PERMISSION_GROUP_UPDATED: [
            subscription_permission_group_updated_webhook,
            permission_group_manage_users,
        ],
        events.PERMISSION_GROUP_DELETED: [
            subscription_permission_group_deleted_webhook,
            permission_group_manage_users,
        ],
        events.SHIPPING_PRICE_CREATED: [
            subscription_shipping_price_created_webhook,
            shipping_method,
        ],
        events.SHIPPING_PRICE_UPDATED: [
            subscription_shipping_price_updated_webhook,
            shipping_method,
        ],
        events.SHIPPING_PRICE_DELETED: [
            subscription_shipping_price_deleted_webhook,
            shipping_method,
        ],
        events.SHIPPING_ZONE_CREATED: [
            subscription_shipping_zone_created_webhook,
            shipping_zone,
        ],
        events.SHIPPING_ZONE_UPDATED: [
            subscription_shipping_zone_updated_webhook,
            shipping_zone,
        ],
        events.SHIPPING_ZONE_DELETED: [
            subscription_shipping_zone_deleted_webhook,
            shipping_zone,
        ],
        events.SHIPPING_ZONE_METADATA_UPDATED: [
            subscription_shipping_zone_metadata_updated_webhook,
            shipping_zone,
        ],
        events.STAFF_CREATED: [subscription_staff_created_webhook, staff_user],
        events.STAFF_UPDATED: [subscription_staff_updated_webhook, staff_user],
        events.STAFF_DELETED: [subscription_staff_deleted_webhook, staff_user],
        events.TRANSACTION_ITEM_METADATA_UPDATED: [
            subscription_transaction_item_metadata_updated_webhook,
            transaction_item,
        ],
        events.TRANSLATION_CREATED: [
            subscription_translation_created_webhook,
            translated_attribute,
        ],
        events.TRANSLATION_UPDATED: [
            subscription_translation_updated_webhook,
            translated_attribute,
        ],
        events.VOUCHER_CREATED: [subscription_voucher_created_webhook, voucher],
        events.VOUCHER_UPDATED: [subscription_voucher_updated_webhook, voucher],
        events.VOUCHER_DELETED: [subscription_voucher_deleted_webhook, voucher],
        events.VOUCHER_METADATA_UPDATED: [
            subscription_voucher_metadata_updated_webhook,
            voucher,
        ],
        events.WAREHOUSE_CREATED: [subscription_warehouse_created_webhook, warehouse],
        events.WAREHOUSE_UPDATED: [subscription_warehouse_updated_webhook, warehouse],
        events.WAREHOUSE_DELETED: [subscription_warehouse_deleted_webhook, warehouse],
        events.WAREHOUSE_METADATA_UPDATED: [
            subscription_warehouse_metadata_updated_webhook,
            warehouse,
        ],
    }


def test_webhook_dry_run_root_type(
    superuser_api_client,
    async_subscription_webhooks_with_root_objects,
):
    # given
    query = WEBHOOK_DRY_RUN_MUTATION

    for event_name, event_type in WEBHOOK_TYPES_MAP.items():
        if not event_type._meta.enable_dry_run:
            continue

        webhook = async_subscription_webhooks_with_root_objects[event_name][0]
        object = async_subscription_webhooks_with_root_objects[event_name][1]
        object_id = graphene.Node.to_global_id(object.__class__.__name__, object.pk)

        variables = {"objectId": object_id, "query": webhook.subscription_query}

        # when
        response = superuser_api_client.post_graphql(query, variables)
        content = get_graphql_content(response)

        # then
        assert not content["data"]["webhookDryRun"]["errors"]
        assert content["data"]["webhookDryRun"]["payload"]
