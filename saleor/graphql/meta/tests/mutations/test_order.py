import graphene

from .....payment.models import TransactionItem
from . import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE
from .test_delete_metadata import (
    execute_clear_public_metadata_for_item,
    item_without_public_metadata,
)
from .test_delete_private_metadata import (
    execute_clear_private_metadata_for_item,
    item_without_private_metadata,
)
from .test_update_metadata import (
    execute_update_public_metadata_for_item,
    item_contains_proper_public_metadata,
)
from .test_update_private_metadata import (
    execute_update_private_metadata_for_item,
    item_contains_proper_private_metadata,
)


def test_delete_public_metadata_for_order_by_id(api_client, order):
    # given
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["metadata"])
    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, order_id, "Order"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], order, order_id
    )


def test_delete_public_metadata_for_order_by_token(api_client, order):
    # given
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["metadata"])
    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, order.id, "Order"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], order, order_id
    )


def test_delete_public_metadata_for_draft_order_by_id(api_client, draft_order):
    # given
    draft_order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    draft_order.save(update_fields=["metadata"])
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, draft_order_id, "Order"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], draft_order, draft_order_id
    )


def test_delete_public_metadata_for_draft_order_by_token(api_client, draft_order):
    # given
    draft_order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    draft_order.save(update_fields=["metadata"])
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, draft_order.id, "Order"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], draft_order, draft_order_id
    )


def test_delete_public_metadata_for_order_line(api_client, order_line):
    # given
    order_line.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order_line.save(update_fields=["metadata"])
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, order_line_id, "OrderLine"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], order_line, order_line_id
    )


def test_delete_private_metadata_for_order_by_id(
    staff_api_client, order, permission_manage_orders
):
    # given
    order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["private_metadata"])
    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, order_id, "Order"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], order, order_id
    )


def test_delete_private_metadata_for_order_by_token(
    staff_api_client, order, permission_manage_orders
):
    # given
    order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["private_metadata"])
    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, order.id, "Order"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], order, order_id
    )


def test_delete_private_metadata_for_draft_order_by_id(
    staff_api_client, draft_order, permission_manage_orders
):
    # given
    draft_order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    draft_order.save(update_fields=["private_metadata"])
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, draft_order_id, "Order"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], draft_order, draft_order_id
    )


def test_delete_private_metadata_for_draft_order_by_token(
    staff_api_client, draft_order, permission_manage_orders
):
    # given
    draft_order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    draft_order.save(update_fields=["private_metadata"])
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, draft_order.id, "Order"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], draft_order, draft_order_id
    )


def test_delete_private_metadata_for_order_line(
    staff_api_client, order_line, permission_manage_orders
):
    # given
    order_line.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    order_line.save(update_fields=["private_metadata"])
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, order_line_id, "OrderLine"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], order_line, order_line_id
    )


def test_add_public_metadata_for_order_by_id(api_client, order):
    # given
    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, order_id, "Order"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], order, order_id
    )


def test_add_public_metadata_for_order_by_token(api_client, order):
    # given
    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, order.id, "Order"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], order, order_id
    )


def test_add_public_metadata_for_draft_order_by_id(api_client, draft_order):
    # given
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, draft_order_id, "Order"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], draft_order, draft_order_id
    )


def test_add_public_metadata_for_draft_order_by_token(api_client, draft_order):
    # given
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, draft_order.id, "Order"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], draft_order, draft_order_id
    )


def test_add_public_metadata_for_order_line(api_client, order_line):
    # given
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, order_line_id, "OrderLine"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], order_line, order_line_id
    )


def test_update_public_metadata_for_order_line(api_client, order_line):
    # given
    order_line.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order_line.save(update_fields=["metadata"])
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, order_line_id, "OrderLine", value="NewMetaValue"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        order_line,
        order_line_id,
        value="NewMetaValue",
    )


def test_add_private_metadata_for_order_by_id(
    staff_api_client, order, permission_manage_orders
):
    # given
    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, order_id, "Order"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], order, order_id
    )


def test_add_private_metadata_for_order_by_token(
    staff_api_client, order, permission_manage_orders
):
    # given
    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, order.id, "Order"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], order, order_id
    )


def test_update_private_metadata_for_order_line(
    staff_api_client, order_line, permission_manage_orders
):
    # given
    order_line.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order_line.save(update_fields=["private_metadata"])
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_orders,
        order_line_id,
        "OrderLine",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        order_line,
        order_line_id,
        value="NewMetaValue",
    )


def test_add_private_metadata_for_draft_order_by_id(
    staff_api_client, draft_order, permission_manage_orders
):
    # given
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, draft_order_id, "Order"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], draft_order, draft_order_id
    )


def test_add_private_metadata_for_draft_order_by_token(
    staff_api_client, draft_order, permission_manage_orders
):
    # given
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, draft_order.id, "Order"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], draft_order, draft_order_id
    )


def test_add_private_metadata_for_order_line(
    staff_api_client, order_line, permission_manage_orders
):
    # given
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, order_line_id, "OrderLine"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], order_line, order_line_id
    )


def test_delete_private_metadata_for_fulfillment(
    staff_api_client, permission_manage_orders, fulfillment
):
    # given
    fulfillment.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    fulfillment.save(update_fields=["private_metadata"])
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, fulfillment_id, "Fulfillment"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], fulfillment, fulfillment_id
    )


def test_delete_public_metadata_for_fulfillment(
    staff_api_client, permission_manage_orders, fulfillment
):
    # given
    fulfillment.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["metadata"])
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_orders, fulfillment_id, "Fulfillment"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], fulfillment, fulfillment_id
    )


def test_delete_public_metadata_for_transaction_item(
    staff_api_client, permission_manage_payments
):
    # given
    transaction_item = TransactionItem.objects.create(
        metadata={PUBLIC_KEY: PUBLIC_VALUE}
    )
    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_payments, transaction_id, "TransactionItem"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], transaction_item, transaction_id
    )


def test_add_public_metadata_for_transaction_item(
    staff_api_client,
    permission_manage_payments,
):
    # given
    transaction_item = TransactionItem.objects.create()
    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_payments, transaction_id, "TransactionItem"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], transaction_item, transaction_id
    )


def test_add_public_metadata_for_fulfillment(
    staff_api_client, permission_manage_orders, fulfillment
):
    # given
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_orders, fulfillment_id, "Fulfillment"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], fulfillment, fulfillment_id
    )


def test_add_private_metadata_for_category(
    staff_api_client, permission_manage_products, category
):
    # given
    category_id = graphene.Node.to_global_id("Category", category.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_products, category_id, "Category"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], category, category_id
    )


def test_add_private_metadata_for_collection(
    staff_api_client, permission_manage_products, published_collection, channel_USD
):
    # given
    collection = published_collection
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_products, collection_id, "Collection"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], collection, collection_id
    )


def test_add_private_metadata_for_digital_content(
    staff_api_client, permission_manage_products, digital_content
):
    # given
    digital_content_id = graphene.Node.to_global_id(
        "DigitalContent", digital_content.pk
    )

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        digital_content_id,
        "DigitalContent",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        digital_content,
        digital_content_id,
    )


def test_add_private_metadata_for_fulfillment(
    staff_api_client, permission_manage_orders, fulfillment
):
    # given
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, fulfillment_id, "Fulfillment"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], fulfillment, fulfillment_id
    )
