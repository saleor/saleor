import graphene

from saleor.core.error_codes import MetaErrorCode
from saleor.core.models import ModelWithMetadata
from tests.api.utils import get_graphql_content

PRIVATE_META_NAMESPACE = "TEST_NAMESPACE"
PUBLIC_META_NAMESPACE = "PUBLIC_NAMESPACE"

META_CLIENT = "TEST_PLUGIN"

PRIVATE_KEY = "name"
PRIVATE_VALUE = "Bond"

PUBLIC_KEY = "purpose"
PUBLIC_VALUE = "42"


UPDATE_PUBLIC_METADATA_MUTATION = """
mutation UpdatePublicMetadata($id: ID!, $input: MetaInput!) {
    updateMeta(
        id: $id
        input: $input
    ) {
        metaErrors{
            field
            code
        }
        item {
            meta {
                namespace
                clients {
                    name
                    metadata {
                        key
                        value
                    }
                }
            }
            ...on %s{
                id
            }
        }
    }
}
"""


def execute_update_public_metadata_for_item(
    client,
    permissions,
    item_id,
    item_type,
    namespace=PUBLIC_META_NAMESPACE,
    client_name=META_CLIENT,
    key=PUBLIC_KEY,
    value=PUBLIC_VALUE,
):
    variables = {
        "id": item_id,
        "input": {
            "namespace": namespace,
            "clientName": client_name,
            "key": key,
            "value": value,
        },
    }

    response = client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


def item_contains_proper_public_metadata(
    response,
    item,
    item_id,
    namespace=PUBLIC_META_NAMESPACE,
    client_name=META_CLIENT,
    key=PUBLIC_KEY,
    value=PUBLIC_VALUE,
):
    if response["data"]["updateMeta"]["item"]["id"] != item_id:
        return False
    item.refresh_from_db()
    meta = item.get_meta(namespace=namespace, client=client_name)
    if meta != {key: value}:
        return False
    return True


def test_add_public_metadata_for_customer_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_contains_proper_public_metadata(response, customer_user, customer_id)


def test_add_public_metadata_for_customer_as_service_account(
    service_account_api_client, permission_manage_users, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_update_public_metadata_for_item(
        service_account_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_contains_proper_public_metadata(response, customer_user, customer_id)


def test_add_public_metadata_for_other_staff_as_staff(
    staff_api_client, permission_manage_staff, admin_user
):
    # given
    assert admin_user.pk != staff_api_client.user.pk
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_staff, admin_id, "User"
    )

    # then
    assert item_contains_proper_public_metadata(response, admin_user, admin_id)


def test_add_public_metadata_for_staff_as_service_account(
    service_account_api_client, permission_manage_staff, admin_user
):
    # given
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_update_public_metadata_for_item(
        service_account_api_client, permission_manage_staff, admin_id, "User"
    )

    # then
    assert item_contains_proper_public_metadata(response, admin_user, admin_id)


def test_add_public_metadata_for_myself_as_customer(user_api_client):
    # given
    customer = user_api_client.user
    customer_id = graphene.Node.to_global_id("User", customer.pk)

    # when
    response = execute_update_public_metadata_for_item(
        user_api_client, None, customer_id, "User"
    )

    # then
    assert item_contains_proper_public_metadata(response, customer, customer_id)


def test_add_public_metadata_for_myself_as_staff(staff_api_client):
    # given
    staff = staff_api_client.user
    staff_id = graphene.Node.to_global_id("User", staff.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, None, staff_id, "User"
    )

    # then
    assert item_contains_proper_public_metadata(response, staff, staff_id)


def test_add_public_metadata_for_checkout(api_client, checkout):
    # given
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout"
    )

    # then
    assert item_contains_proper_public_metadata(response, checkout, checkout_id)


def test_add_public_metadata_for_order(api_client, order):
    # given
    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, order_id, "Order"
    )

    # then
    assert item_contains_proper_public_metadata(response, order, order_id)


def test_add_public_metadata_for_attribute(
    staff_api_client, permission_manage_products, color_attribute
):
    # given
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_products, attribute_id, "Attribute"
    )

    # then
    assert item_contains_proper_public_metadata(response, color_attribute, attribute_id)


def test_add_public_metadata_for_category(
    staff_api_client, permission_manage_products, category
):
    # given
    category_id = graphene.Node.to_global_id("Category", category.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_products, category_id, "Category"
    )

    # then
    assert item_contains_proper_public_metadata(response, category, category_id)


def test_add_public_metadata_for_collection(
    staff_api_client, permission_manage_products, collection
):
    # given
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_products, collection_id, "Collection"
    )

    # then
    assert item_contains_proper_public_metadata(response, collection, collection_id)


def test_add_public_metadata_for_digital_content(
    staff_api_client, permission_manage_products, digital_content
):
    # given
    digital_content_id = graphene.Node.to_global_id(
        "DigitalContent", digital_content.pk
    )

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        digital_content_id,
        "DigitalContent",
    )

    # then
    assert item_contains_proper_public_metadata(
        response, digital_content, digital_content_id
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
    assert item_contains_proper_public_metadata(response, fulfillment, fulfillment_id)


def test_add_public_metadata_for_product(
    staff_api_client, permission_manage_products, product
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_products, product_id, "Product"
    )

    # then
    assert item_contains_proper_public_metadata(response, product, product_id)


def test_add_public_metadata_for_product_type(
    staff_api_client, permission_manage_products, product_type
):
    # given
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_products, product_type_id, "ProductType"
    )

    # then
    assert item_contains_proper_public_metadata(response, product_type, product_type_id)


def test_add_public_metadata_for_product_variant(
    staff_api_client, permission_manage_products, product_type
):
    # given
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_products, product_type_id, "ProductType"
    )

    # then
    assert item_contains_proper_public_metadata(response, product_type, product_type_id)


def test_add_public_metadata_for_service_account(
    staff_api_client, permission_manage_service_accounts, service_account
):
    # given
    service_account_id = graphene.Node.to_global_id(
        "ServiceAccount", service_account.pk
    )

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_service_accounts,
        service_account_id,
        "ServiceAccount",
    )

    # then
    assert item_contains_proper_public_metadata(
        response, service_account, service_account_id
    )


def test_update_public_metadata_for_item(api_client, checkout):
    # given
    checkout.store_meta(PUBLIC_META_NAMESPACE, META_CLIENT, {PUBLIC_KEY: PUBLIC_VALUE})
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout", value="NewMetaValue"
    )

    # then
    assert item_contains_proper_public_metadata(
        response, checkout, checkout_id, value="NewMetaValue"
    )


def test_update_public_metadata_for_non_exist_item(api_client):
    # given
    checkout_id = "Q2hlY2tvdXQ6SU5WQUxJRA=="

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout"
    )

    # then
    errors = response["data"]["updateMeta"]["metaErrors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetaErrorCode.NOT_FOUND.name


def test_update_public_metadata_for_item_without_meta(api_client, address):
    # given
    assert not issubclass(type(address), ModelWithMetadata)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    # We use "User" type inside mutation for valid graphql query with fragment
    # without this we are not able to reuse UPDATE_PUBLIC_METADATA_MUTATION
    response = execute_update_public_metadata_for_item(
        api_client, None, address_id, "User"
    )

    # then
    errors = response["data"]["updateMeta"]["metaErrors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetaErrorCode.INVALID.name
