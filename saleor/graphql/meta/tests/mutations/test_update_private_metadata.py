import base64
from unittest.mock import patch

import graphene
import pytest

from .....core.error_codes import MetadataErrorCode
from .....core.jwt import create_access_token_for_app
from .....core.models import ModelWithMetadata
from .....invoice.models import Invoice
from .....payment.models import TransactionItem
from ....tests.fixtures import ApiClient
from ....tests.utils import assert_no_permission, get_graphql_content

PRIVATE_KEY = "private_key"
PRIVATE_VALUE = "private_vale"

PUBLIC_KEY = "key"
PUBLIC_KEY2 = "key2"
PUBLIC_VALUE = "value"
PUBLIC_VALUE2 = "value2"


UPDATE_PRIVATE_METADATA_MUTATION = """
mutation UpdatePrivateMetadata($id: ID!, $input: [MetadataInput!]!) {
    updatePrivateMetadata(
        id: $id
        input: $input
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


def execute_update_private_metadata_for_item(
    client,
    permissions,
    item_id,
    item_type,
    key=PRIVATE_KEY,
    value=PRIVATE_VALUE,
):
    variables = {
        "id": item_id,
        "input": [{"key": key, "value": value}],
    }

    response = client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


def execute_update_private_metadata_for_multiple_items(
    client,
    permissions,
    item_id,
    item_type,
    key=PUBLIC_KEY,
    value=PUBLIC_VALUE,
    key2=PUBLIC_KEY2,
    value2=PUBLIC_VALUE2,
):
    variables = {
        "id": item_id,
        "input": [{"key": key, "value": value}, {"key": key2, "value": value2}],
    }

    response = client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


def item_contains_proper_private_metadata(
    item_from_response,
    item,
    item_id,
    key=PRIVATE_KEY,
    value=PRIVATE_VALUE,
):
    if item_from_response["id"] != item_id:
        return False
    item.refresh_from_db()
    return item.get_value_from_private_metadata(key) == value


def item_contains_multiple_proper_private_metadata(
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
            item.get_value_from_private_metadata(key) == value,
            item.get_value_from_private_metadata(key2) == value2,
        ]
    )


def test_add_private_metadata_for_customer_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], customer_user, customer_id
    )


def test_add_private_metadata_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_update_private_metadata_for_item(
        app_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], customer_user, customer_id
    )


def test_add_multiple_private_metadata_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_update_private_metadata_for_multiple_items(
        app_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_contains_multiple_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], customer_user, customer_id
    )


def test_add_private_metadata_for_other_staff_as_staff(
    staff_api_client, permission_manage_staff, admin_user
):
    # given
    assert admin_user.pk != staff_api_client.user.pk
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_staff, admin_id, "User"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], admin_user, admin_id
    )


def test_add_public_metadata_for_staff_as_app_no_permission(
    app_api_client, permission_manage_staff, admin_user
):
    # given
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)
    variables = {
        "id": admin_id,
        "input": [{"key": PUBLIC_KEY, "value": PUBLIC_VALUE}],
    }

    # when

    response = app_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "User",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_add_private_metadata_for_invoice(staff_api_client, permission_manage_orders):
    # given
    invoice = Invoice.objects.create(number="1/7/2020")
    invoice_id = graphene.Node.to_global_id("Invoice", invoice.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_orders, invoice_id, "Invoice"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], invoice, invoice_id
    )


def test_add_private_metadata_for_staff_as_app_no_permission(
    app_api_client, permission_manage_staff, admin_user
):
    # given
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)
    variables = {
        "id": admin_id,
        "input": [{"key": PRIVATE_KEY, "value": PRIVATE_VALUE}],
    }

    # when
    response = app_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "User",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_add_private_metadata_for_myself_as_customer_no_permission(user_api_client):
    # given
    customer = user_api_client.user
    variables = {
        "id": graphene.Node.to_global_id("User", customer.pk),
        "input": [{"key": PRIVATE_KEY, "value": PRIVATE_VALUE}],
    }

    # when
    response = user_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "User",
        variables,
        permissions=[],
    )

    # then
    assert_no_permission(response)


@pytest.mark.parametrize(
    "input",
    [{"key": " ", "value": "test"}, {"key": "   ", "value": ""}],
)
def test_staff_update_private_metadata_empty_key(
    input, staff_api_client, permission_manage_staff, admin_user
):
    # given
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_staff,
        admin_id,
        "User",
        input["key"],
        input["value"],
    )

    # then
    data = response["data"]["updatePrivateMetadata"]
    errors = data["errors"]

    assert not data["item"]
    assert len(errors) == 1
    assert errors[0]["code"] == MetadataErrorCode.REQUIRED.name
    assert errors[0]["field"] == "input"


def test_add_private_metadata_for_myself_as_staff(staff_api_client):
    # given
    staff = staff_api_client.user
    variables = {
        "id": graphene.Node.to_global_id("User", staff.pk),
        "input": [{"key": PRIVATE_KEY, "value": PRIVATE_VALUE}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "User",
        variables,
        permissions=[],
    )

    # then
    assert_no_permission(response)


def test_add_private_metadata_for_checkout(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout_id, "Checkout"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_add_private_metadata_for_checkout_no_checkout_metadata_storage(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout.metadata_storage.delete()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout_id, "Checkout"
    )

    # then
    checkout.refresh_from_db()
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_add_private_metadata_for_checkout_line(
    staff_api_client, checkout_line, permission_manage_checkouts
):
    # given
    checkout_line_id = graphene.Node.to_global_id("CheckoutLine", checkout_line.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout_line_id, "CheckoutLine"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        checkout_line,
        checkout_line_id,
    )


def test_add_private_metadata_for_checkout_by_token(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout.token, "Checkout"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
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


def test_add_private_metadata_for_product_attribute(
    staff_api_client, permission_manage_product_types_and_attributes, color_attribute
):
    # given
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_product_types_and_attributes,
        attribute_id,
        "Attribute",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], color_attribute, attribute_id
    )


def test_add_private_metadata_for_page_attribute(
    staff_api_client, permission_manage_page_types_and_attributes, size_page_attribute
):
    # given
    attribute_id = graphene.Node.to_global_id("Attribute", size_page_attribute.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_page_types_and_attributes,
        attribute_id,
        "Attribute",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        size_page_attribute,
        attribute_id,
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


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_add_private_metadata_for_product(
    updated_webhook_mock, staff_api_client, permission_manage_products, product
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_products, product_id, "Product"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], product, product_id
    )
    updated_webhook_mock.assert_called_once_with(product)


def test_add_private_metadata_for_product_type(
    staff_api_client, permission_manage_product_types_and_attributes, product_type
):
    # given
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_product_types_and_attributes,
        product_type_id,
        "ProductType",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], product_type, product_type_id
    )


def test_add_private_metadata_for_product_variant(
    staff_api_client, permission_manage_products, variant
):
    # given
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        variant_id,
        "ProductVariant",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], variant, variant_id
    )


def test_add_private_metadata_for_app(staff_api_client, permission_manage_apps, app):
    # given
    app_id = graphene.Node.to_global_id("App", app.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_apps,
        app_id,
        "App",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        app,
        app_id,
    )


def test_add_private_metadata_for_app_by_different_app(
    app_api_client, permission_manage_apps, app, payment_app
):
    # given
    app_id = graphene.Node.to_global_id("App", payment_app.pk)
    app_api_client.app = app

    # when
    response = execute_update_private_metadata_for_item(
        app_api_client,
        permission_manage_apps,
        app_id,
        "App",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        payment_app,
        app_id,
    )


def test_add_private_metadata_for_app_with_app_user_token(
    staff_user, permission_manage_apps, app, payment_app
):
    # given
    token = create_access_token_for_app(app, staff_user)
    api_client = ApiClient(user=staff_user)
    api_client.token = token
    app_id = graphene.Node.to_global_id("App", app.pk)

    variables = {
        "id": app_id,
        "input": [{"key": PUBLIC_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "App", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_add_private_metadata_by_app_that_is_owner(
    app_api_client, permission_manage_apps, app
):
    # given
    app_id = graphene.Node.to_global_id("App", app.pk)
    app_api_client.app = app

    # when
    response = execute_update_private_metadata_for_item(
        app_api_client,
        None,
        app_id,
        "App",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        app,
        app_id,
    )


def test_add_private_metadata_for_page(staff_api_client, permission_manage_pages, page):
    # given
    page_id = graphene.Node.to_global_id("Page", page.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_pages,
        page_id,
        "Page",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        page,
        page_id,
    )


def test_add_private_metadata_for_shipping_method(
    staff_api_client, permission_manage_shipping, shipping_method
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_shipping,
        shipping_method_id,
        "ShippingMethodType",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        shipping_method,
        shipping_method_id,
    )


def test_add_private_metadata_for_shipping_zone(
    staff_api_client, permission_manage_shipping, shipping_zone
):
    # given
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_shipping,
        shipping_zone_id,
        "ShippingZone",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        shipping_zone,
        shipping_zone_id,
    )


def test_add_private_metadata_for_menu(staff_api_client, permission_manage_menus, menu):
    # given
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_menus,
        menu_id,
        "Menu",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        menu,
        menu_id,
    )


def test_add_private_metadata_for_menu_item(
    staff_api_client, permission_manage_menus, menu_item
):
    # given
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_menus,
        menu_item_id,
        "MenuItem",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        menu_item,
        menu_item_id,
    )


def test_update_private_metadata_for_item(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout.metadata_storage.store_value_in_private_metadata(
        {PRIVATE_KEY: PRIVATE_KEY}
    )
    checkout.metadata_storage.save(update_fields=["private_metadata"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_checkouts,
        checkout.token,
        "Checkout",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
        value="NewMetaValue",
    )


def test_update_private_metadata_for_non_exist_item(
    staff_api_client, permission_manage_payments
):
    # given
    payment_id = "Payment: 0"
    payment_id = base64.b64encode(str.encode(payment_id)).decode("utf-8")

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_payments, payment_id, "Payment"
    )

    # then
    errors = response["data"]["updatePrivateMetadata"]["errors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetadataErrorCode.NOT_FOUND.name


def test_update_private_metadata_for_item_without_meta(
    api_client, permission_group_manage_users
):
    # given
    group = permission_group_manage_users
    assert not issubclass(type(group), ModelWithMetadata)
    group_id = graphene.Node.to_global_id("Group", group.pk)

    # when
    # We use "User" type inside mutation for valid graphql query with fragment
    # without this we are not able to reuse UPDATE_PRIVATE_METADATA_MUTATION
    response = execute_update_private_metadata_for_item(
        api_client, None, group_id, "User"
    )

    # then
    errors = response["data"]["updatePrivateMetadata"]["errors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetadataErrorCode.NOT_FOUND.name


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


def test_update_private_metadata_by_customer(user_api_client, payment):
    # given
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {
        "id": payment_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = user_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Payment", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_checkout_line(
    staff_api_client, checkout_line, permission_manage_checkouts
):
    # given
    checkout_line.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    checkout_line.save(update_fields=["private_metadata"])
    checkout_line_id = graphene.Node.to_global_id("CheckoutLine", checkout_line.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_checkouts,
        checkout_line_id,
        "CheckoutLine",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        checkout_line,
        checkout_line_id,
        value="NewMetaValue",
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


def test_add_private_metadata_for_warehouse(
    staff_api_client, permission_manage_products, warehouse
):
    # given
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_products, warehouse_id, "Warehouse"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], warehouse, warehouse_id
    )


def test_add_private_metadata_for_gift_card(
    staff_api_client, permission_manage_gift_card, gift_card
):
    # given
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_gift_card, gift_card_id, "GiftCard"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], gift_card, gift_card_id
    )


def test_update_private_metadata_for_customer_address_by_logged_user(
    user_api_client, address
):
    # given
    user = user_api_client.user
    user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = user_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_customer_address_by_different_logged_user(
    user2_api_client, customer_user
):
    # given
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = user2_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_customer_address_by_staff_with_perm(
    staff_api_client, customer_user, permission_manage_users
):
    # given
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_users,
        address_id,
        "Address",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        address,
        address_id,
        value="NewMetaValue",
    )


def test_update_private_metadata_for_customer_address_by_app_with_perm(
    app_api_client, customer_user, permission_manage_users
):
    # given
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_update_private_metadata_for_item(
        app_api_client,
        permission_manage_users,
        address_id,
        "Address",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        address,
        address_id,
        value="NewMetaValue",
    )


def test_update_private_metadata_for_address_by_non_logged_user(
    api_client, customer_user
):
    # given
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id("Address", address.pk)
    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_staff_address_by_staff_with_perm(
    staff_api_client, address, staff_users, permission_manage_staff
):
    # given
    user = staff_users[-1]
    user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_staff,
        address_id,
        "Address",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        address,
        address_id,
        value="NewMetaValue",
    )


def test_update_private_metadata_for_staff_address_by_staff_without_perm(
    staff_api_client, address, staff_users
):
    # given
    user = staff_users[-1]
    user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_staff_address_by_customer(
    user_api_client, address, staff_users
):
    # given
    user = staff_users[-1]
    user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = user_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_staff_address_by_app_with_perm(
    app_api_client, staff_user, address, permission_manage_staff
):
    # given
    staff_user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = app_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_staff_address_by_app_without_perm(
    app_api_client, staff_user, address
):
    # given
    staff_user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = app_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address", variables
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_warehouse_address_by_staff(
    staff_api_client, warehouse, permission_manage_staff
):
    # given
    address = warehouse.address
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_site_settings_address_by_staff(
    staff_api_client, site_settings, address, permission_manage_staff
):
    # given
    site_settings.company_address = address
    site_settings.save(update_fields=["company_address"])

    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_add_private_metadata_for_product_media(
    staff_api_client, permission_manage_products, product_with_image
):
    # given
    media = product_with_image.media.first()
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_products, media_id, "ProductMedia"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], media, media_id
    )


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


def test_add_private_metadata_for_sale(
    staff_api_client, permission_manage_discounts, sale
):
    # given
    sale_id = graphene.Node.to_global_id("Sale", sale.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_discounts, sale_id, "Sale"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], sale, sale_id
    )


def test_add_private_metadata_for_voucher(
    staff_api_client, permission_manage_discounts, voucher
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_discounts, voucher_id, "Voucher"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], voucher, voucher_id
    )
