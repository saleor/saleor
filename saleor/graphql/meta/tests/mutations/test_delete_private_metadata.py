import base64
from unittest.mock import patch

import graphene

from .....core.error_codes import MetadataErrorCode
from .....core.models import ModelWithMetadata
from .....payment.models import TransactionItem
from ....tests.utils import assert_no_permission, get_graphql_content
from .test_update_private_metadata import item_contains_proper_private_metadata

PRIVATE_KEY = "private_key"
PRIVATE_VALUE = "private_vale"

PUBLIC_KEY = "key"
PUBLIC_KEY2 = "key2"
PUBLIC_VALUE = "value"
PUBLIC_VALUE2 = "value2"

DELETE_PRIVATE_METADATA_MUTATION = """
mutation DeletePrivateMetadata($id: ID!, $keys: [String!]!) {
    deletePrivateMetadata(
        id: $id
        keys: $keys
    ) {
        errors{
            field
            code
        }
        item {
            privateMetadata{
                key
                value
            }
            ...on %s{
                id
            }
        }
    }
}
"""


def execute_clear_private_metadata_for_item(
    client,
    permissions,
    item_id,
    item_type,
    key=PRIVATE_KEY,
):
    variables = {
        "id": item_id,
        "keys": [key],
    }

    response = client.post_graphql(
        DELETE_PRIVATE_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


def execute_clear_private_metadata_for_multiple_items(
    client, permissions, item_id, item_type, key=PUBLIC_KEY, key2=PUBLIC_KEY2
):
    variables = {
        "id": item_id,
        "keys": [key, key2],
    }

    response = client.post_graphql(
        DELETE_PRIVATE_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


def item_without_private_metadata(
    item_from_response,
    item,
    item_id,
    key=PRIVATE_KEY,
    value=PRIVATE_VALUE,
):
    if item_from_response["id"] != item_id:
        return False
    item.refresh_from_db()
    return item.get_value_from_private_metadata(key) != value


def item_without_multiple_private_metadata(
    item_from_response,
    item,
    item_id,
    key=PUBLIC_KEY,
    value=PUBLIC_VALUE,
    key2=PUBLIC_KEY2,
    value2=PUBLIC_VALUE2,
):
    if item_from_response["id"] != item_id:
        return False
    item.refresh_from_db()
    return all(
        [
            item.get_value_from_private_metadata(key) != value,
            item.get_value_from_private_metadata(key2) != value2,
        ]
    )


def test_delete_private_metadata_for_customer_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    customer_user.save(update_fields=["private_metadata"])
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], customer_user, customer_id
    )


def test_delete_private_metadata_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    customer_user.save(update_fields=["private_metadata"])
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        app_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], customer_user, customer_id
    )


def test_delete_multiple_private_metadata_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_metadata(
        {PUBLIC_KEY: PUBLIC_VALUE, PUBLIC_KEY2: PUBLIC_VALUE2}
    )
    customer_user.save(update_fields=["metadata"])
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_clear_private_metadata_for_multiple_items(
        app_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_without_multiple_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], customer_user, customer_id
    )


def test_delete_private_metadata_for_other_staff_as_staff(
    staff_api_client, permission_manage_staff, admin_user
):
    # given
    assert admin_user.pk != staff_api_client.user.pk
    admin_user.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    admin_user.save(update_fields=["private_metadata"])
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_staff, admin_id, "User"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], admin_user, admin_id
    )


def test_delete_private_metadata_for_staff_as_app_no_permission(
    app_api_client, permission_manage_staff, admin_user
):
    # given
    admin_user.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    admin_user.save(update_fields=["private_metadata"])
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)
    variables = {
        "id": admin_id,
        "keys": [PRIVATE_KEY],
    }

    # when
    response = app_api_client.post_graphql(
        DELETE_PRIVATE_METADATA_MUTATION % "User",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_delete_private_metadata_for_myself_as_customer_no_permission(user_api_client):
    # given
    customer = user_api_client.user
    customer.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    customer.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("User", customer.pk),
        "keys": [PRIVATE_KEY],
    }

    # when
    response = user_api_client.post_graphql(
        DELETE_PRIVATE_METADATA_MUTATION % "User", variables, permissions=[]
    )

    # then
    assert_no_permission(response)


def test_delete_private_metadata_for_myself_as_staff_no_permission(
    staff_api_client, permission_manage_users
):
    # given
    staff = staff_api_client.user
    staff.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    staff.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("User", staff.pk),
        "keys": [PRIVATE_KEY],
    }

    # when
    response = staff_api_client.post_graphql(
        DELETE_PRIVATE_METADATA_MUTATION % "User",
        variables,
        permissions=[permission_manage_users],
    )

    # then
    assert_no_permission(response)


def test_delete_private_metadata_for_checkout(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout.metadata_storage.store_value_in_private_metadata(
        {PRIVATE_KEY: PRIVATE_VALUE}
    )
    checkout.metadata_storage.save(update_fields=["private_metadata"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout_id, "Checkout"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_delete_private_metadata_for_checkout_by_token(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout.metadata_storage.store_value_in_private_metadata(
        {PRIVATE_KEY: PRIVATE_VALUE}
    )
    checkout.metadata_storage.save(update_fields=["private_metadata"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout.token, "Checkout"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_delete_private_metadata_for_checkout_line(
    staff_api_client, checkout_line, permission_manage_checkouts
):
    # given
    checkout_line.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    checkout_line.save(update_fields=["private_metadata"])
    checkout_line_id = graphene.Node.to_global_id("CheckoutLine", checkout_line.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout_line_id, "CheckoutLine"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        checkout_line,
        checkout_line_id,
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


def test_delete_private_metadata_for_product_attribute(
    staff_api_client, permission_manage_product_types_and_attributes, color_attribute
):
    # given
    color_attribute.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    color_attribute.save(update_fields=["private_metadata"])
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_product_types_and_attributes,
        attribute_id,
        "Attribute",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], color_attribute, attribute_id
    )


def test_delete_private_metadata_for_page_attribute(
    staff_api_client, permission_manage_page_types_and_attributes, size_page_attribute
):
    # given
    size_page_attribute.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    size_page_attribute.save(update_fields=["private_metadata"])
    attribute_id = graphene.Node.to_global_id("Attribute", size_page_attribute.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_page_types_and_attributes,
        attribute_id,
        "Attribute",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        size_page_attribute,
        attribute_id,
    )


def test_delete_private_metadata_for_category(
    staff_api_client, permission_manage_products, category
):
    # given
    category.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    category.save(update_fields=["private_metadata"])
    category_id = graphene.Node.to_global_id("Category", category.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, category_id, "Category"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], category, category_id
    )


def test_delete_private_metadata_for_collection(
    staff_api_client, permission_manage_products, published_collection, channel_USD
):
    # given
    collection = published_collection
    collection.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    collection.save(update_fields=["private_metadata"])
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, collection_id, "Collection"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], collection, collection_id
    )


def test_delete_private_metadata_for_digital_content(
    staff_api_client, permission_manage_products, digital_content
):
    # given
    digital_content.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    digital_content.save(update_fields=["private_metadata"])
    digital_content_id = graphene.Node.to_global_id(
        "DigitalContent", digital_content.pk
    )

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        digital_content_id,
        "DigitalContent",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        digital_content,
        digital_content_id,
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


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_delete_private_metadata_for_product(
    updated_webhook_mock, staff_api_client, permission_manage_products, product
):
    # given
    product.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    product.save(update_fields=["private_metadata"])
    product_id = graphene.Node.to_global_id("Product", product.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, product_id, "Product"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], product, product_id
    )
    updated_webhook_mock.assert_called_once_with(product)


def test_delete_private_metadata_for_product_type(
    staff_api_client, permission_manage_product_types_and_attributes, product_type
):
    # given
    product_type.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    product_type.save(update_fields=["private_metadata"])
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_product_types_and_attributes,
        product_type_id,
        "ProductType",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], product_type, product_type_id
    )


def test_delete_private_metadata_for_product_variant(
    staff_api_client, permission_manage_products, variant
):
    # given
    variant.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    variant.save(update_fields=["private_metadata"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, variant_id, "ProductVariant"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], variant, variant_id
    )


def test_delete_private_metadata_for_app(staff_api_client, permission_manage_apps, app):
    # given
    app.store_value_in_private_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    app.save(update_fields=["private_metadata"])
    app_id = graphene.Node.to_global_id("App", app.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_apps,
        app_id,
        "App",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        app,
        app_id,
    )


def test_delete_private_metadata_for_page(
    staff_api_client, permission_manage_pages, page
):
    # given
    page.store_value_in_private_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    page.save(update_fields=["private_metadata"])
    page_id = graphene.Node.to_global_id("Page", page.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_pages,
        page_id,
        "Page",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        page,
        page_id,
    )


def test_delete_private_metadata_for_shipping_method(
    staff_api_client, permission_manage_shipping, shipping_method
):
    # given
    shipping_method.store_value_in_private_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    shipping_method.save(update_fields=["metadata"])
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_shipping,
        shipping_method_id,
        "ShippingMethodType",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        shipping_method,
        shipping_method_id,
    )


def test_delete_private_metadata_for_shipping_zone(
    staff_api_client, permission_manage_shipping, shipping_zone
):
    # given
    shipping_zone.store_value_in_private_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    shipping_zone.save(update_fields=["metadata"])
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_shipping,
        shipping_zone_id,
        "ShippingZone",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        shipping_zone,
        shipping_zone_id,
    )


def test_delete_private_metadata_for_menu(
    staff_api_client, permission_manage_menus, menu
):
    # given
    menu.store_value_in_private_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    menu.save(update_fields=["metadata"])
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_menus,
        menu_id,
        "Menu",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        menu,
        menu_id,
    )


def test_delete_private_metadata_for_menu_item(
    staff_api_client, permission_manage_menus, menu_item
):
    # given
    menu_item.store_value_in_private_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    menu_item.save(update_fields=["metadata"])
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_menus,
        menu_item_id,
        "MenuItem",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        menu_item,
        menu_item_id,
    )


def test_delete_private_metadata_for_non_exist_item(
    staff_api_client, permission_manage_payments
):
    # given
    payment_id = "Payment: 0"
    payment_id = base64.b64encode(str.encode(payment_id)).decode("utf-8")

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_payments, payment_id, "Payment"
    )

    # then
    errors = response["data"]["deletePrivateMetadata"]["errors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetadataErrorCode.NOT_FOUND.name


def test_delete_private_metadata_for_item_without_meta(
    api_client, permission_group_manage_users
):
    # given
    group = permission_group_manage_users
    assert not issubclass(type(group), ModelWithMetadata)
    group_id = graphene.Node.to_global_id("Group", group.pk)

    # when
    # We use "User" type inside mutation for valid graphql query with fragment
    # without this we are not able to reuse DELETE_PRIVATE_METADATA_MUTATION
    response = execute_clear_private_metadata_for_item(
        api_client, None, group_id, "User"
    )

    # then
    errors = response["data"]["deletePrivateMetadata"]["errors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetadataErrorCode.NOT_FOUND.name


def test_delete_private_metadata_for_not_exist_key(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout.metadata_storage.store_value_in_private_metadata(
        {PRIVATE_KEY: PRIVATE_VALUE}
    )
    checkout.metadata_storage.save(update_fields=["private_metadata"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_checkouts,
        checkout.token,
        "Checkout",
        key="Not-exits",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_delete_private_metadata_for_one_key(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout.metadata_storage.store_value_in_private_metadata(
        {PRIVATE_KEY: PRIVATE_VALUE, "to_clear": PRIVATE_VALUE},
    )
    checkout.metadata_storage.save(update_fields=["private_metadata"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_checkouts,
        checkout.token,
        "Checkout",
        key="to_clear",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
        key="to_clear",
    )


def test_delete_private_metadata_for_warehouse(
    staff_api_client, permission_manage_products, warehouse
):
    # given
    warehouse.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    warehouse.save(update_fields=["private_metadata"])
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, warehouse_id, "Warehouse"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], warehouse, warehouse_id
    )


def test_delete_private_metadata_for_gift_card(
    staff_api_client, permission_manage_gift_card, gift_card
):
    # given
    gift_card.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    gift_card.save(update_fields=["private_metadata"])
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_gift_card, gift_card_id, "GiftCard"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], gift_card, gift_card_id
    )


def test_delete_private_metadata_for_product_media(
    staff_api_client, permission_manage_products, product_with_image
):
    # given
    media = product_with_image.media.first()
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    media.store_value_in_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    media.save(update_fields=["private_metadata"])

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, media_id, "ProductMedia"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], media, media_id
    )


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


def test_delete_private_metadata_for_voucher(
    staff_api_client, permission_manage_discounts, voucher
):
    # given
    voucher.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    voucher.save(update_fields=["private_metadata"])
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_discounts, voucher_id, "Voucher"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], voucher, voucher_id
    )


def test_delete_private_metadata_for_sale(
    staff_api_client, permission_manage_discounts, sale
):
    # given
    sale.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    sale.save(update_fields=["private_metadata"])
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_discounts, sale_id, "Sale"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], sale, sale_id
    )


def test_delete_private_metadata_for_customer_address_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    address = customer_user.addresses.first()
    address.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    address.save(update_fields=["private_metadata"])
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_users, address_id, "Address"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], address, address_id
    )


def test_delete_private_metadata_for_customer_address_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    address = customer_user.addresses.first()
    address.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    address.save(update_fields=["private_metadata"])
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        app_api_client, permission_manage_users, address_id, "Address"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], address, address_id
    )


def test_delete_private_metadata_for_staff_address_as_staff(
    staff_api_client, address, permission_manage_staff
):
    # given
    staff_user = staff_api_client.user
    staff_user.addresses.add(address)
    address.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    address.save(update_fields=["private_metadata"])
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_staff, address_id, "Address"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], address, address_id
    )


def test_delete_private_metadata_for_staff_address_as_app(
    app_api_client, staff_user, address, permission_manage_staff
):
    # given
    staff_user.addresses.add(address)
    address.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    address.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Address", address.pk),
        "keys": [PRIVATE_KEY],
    }

    # when
    response = app_api_client.post_graphql(
        DELETE_PRIVATE_METADATA_MUTATION % "Address",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_delete_private_metadata_for_myself_address_as_staff_no_permission(
    staff_api_client, address, permission_manage_users
):
    # given
    staff = staff_api_client.user
    staff.addresses.add(address)
    staff.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    staff.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Address", address.pk),
        "keys": [PRIVATE_KEY],
    }

    # when
    response = staff_api_client.post_graphql(
        DELETE_PRIVATE_METADATA_MUTATION % "Address",
        variables,
        permissions=[permission_manage_users],
    )

    # then
    assert_no_permission(response)
