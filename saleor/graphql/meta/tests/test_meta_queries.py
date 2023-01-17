from typing import List

import graphene
from django.http import HttpResponse

from ....core.models import ModelWithMetadata
from ....order.models import Order
from ....payment.models import Payment
from ....payment.utils import payment_owned_by_user
from ....permission.models import Permission
from ...tests.fixtures import ApiClient
from ...tests.utils import assert_no_permission, get_graphql_content

PRIVATE_KEY = "private_key"
PRIVATE_VALUE = "private_vale"

PUBLIC_KEY = "key"
PUBLIC_VALUE = "value"


def execute_query(
    query_str: str,
    client: ApiClient,
    model: ModelWithMetadata,
    model_name: str,
    permissions: List[Permission] = None,
):
    return client.post_graphql(
        query_str,
        variables={"id": graphene.Node.to_global_id(model_name, model.pk)},
        permissions=[] if permissions is None else permissions,
        check_no_permissions=False,
    )


def assert_model_contains_metadata(response: HttpResponse, model_name: str):
    content = get_graphql_content(response)
    metadata = content["data"][model_name]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def assert_model_contains_private_metadata(response: HttpResponse, model_name: str):
    content = get_graphql_content(response)
    metadata = content["data"][model_name]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_SELF_PUBLIC_META = """
    {
        me{
            metadata{
                key
                value
            }
            metafields(keys: ["INVALID", "key"])
            keyFieldValue: metafield(key: "key")
        }
    }
"""


def test_query_public_meta_for_me_as_customer(user_api_client):
    # given
    me = user_api_client.user
    me.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    me.save(update_fields=["metadata"])

    # when
    response = user_api_client.post_graphql(QUERY_SELF_PUBLIC_META)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["me"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE
    metafields = content["data"]["me"]["metafields"]
    assert metafields[PUBLIC_KEY] == PUBLIC_VALUE
    field_value = content["data"]["me"]["keyFieldValue"]
    assert field_value == PUBLIC_VALUE


def test_query_public_meta_for_me_as_staff(staff_api_client):
    # given
    me = staff_api_client.user
    me.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    me.save(update_fields=["metadata"])

    # when
    response = staff_api_client.post_graphql(QUERY_SELF_PUBLIC_META)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["me"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE
    metafields = content["data"]["me"]["metafields"]
    assert metafields[PUBLIC_KEY] == PUBLIC_VALUE
    field_value = content["data"]["me"]["keyFieldValue"]
    assert field_value == PUBLIC_VALUE


QUERY_USER_PUBLIC_META = """
    query userMeta($id: ID!){
        user(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_customer_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    customer_user.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_USER_PUBLIC_META, variables, [permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["user"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    customer_user.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_USER_PUBLIC_META, variables, [permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["user"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_staff_as_other_staff(
    staff_api_client, permission_manage_staff, admin_user
):
    # given
    admin_user.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    admin_user.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("User", admin_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_USER_PUBLIC_META, variables, [permission_manage_staff]
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["user"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_CHECKOUT_PUBLIC_META = """
    query checkoutMeta($token: UUID!){
        checkout(token: $token){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_checkout_as_anonymous_user(api_client, checkout):
    # given
    checkout.metadata_storage.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.metadata_storage.save(update_fields=["metadata"])
    variables = {"token": checkout.pk}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["checkout"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_other_customer_checkout_as_anonymous_user(
    api_client, checkout, customer_user
):
    # given
    checkout.user = customer_user
    checkout.metadata_storage.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.save(update_fields=["user"])
    checkout.metadata_storage.save(update_fields=["metadata"])
    variables = {"token": checkout.pk}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkout"]


def test_query_public_meta_for_checkout_as_customer(user_api_client, checkout):
    # given
    checkout.user = user_api_client.user
    checkout.metadata_storage.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.save(update_fields=["user"])
    checkout.metadata_storage.save(update_fields=["metadata"])
    variables = {"token": checkout.pk}

    # when
    response = user_api_client.post_graphql(QUERY_CHECKOUT_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["checkout"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_checkout_as_staff(
    staff_api_client, checkout, customer_user, permission_manage_checkouts
):
    # given
    checkout.user = customer_user
    checkout.metadata_storage.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.save(update_fields=["user"])
    checkout.metadata_storage.save(update_fields=["metadata"])
    variables = {"token": checkout.pk}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CHECKOUT_PUBLIC_META,
        variables,
        [permission_manage_checkouts],
        check_no_permissions=False,  # Remove after fix #5245
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["checkout"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_checkout_as_app(
    app_api_client, checkout, customer_user, permission_manage_checkouts
):
    # given
    checkout.user = customer_user
    checkout.metadata_storage.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.save(update_fields=["user"])
    checkout.metadata_storage.save(update_fields=["metadata"])
    variables = {"token": checkout.pk}

    # when
    response = app_api_client.post_graphql(
        QUERY_CHECKOUT_PUBLIC_META,
        variables,
        [permission_manage_checkouts],
        check_no_permissions=False,  # Remove after fix #5245
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["checkout"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_ORDER_BY_TOKEN_PUBLIC_META = """
    query orderMeta($token: UUID!){
        orderByToken(token: $token){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_order_by_token_as_anonymous_user(api_client, order):
    # given
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["metadata"])
    variables = {"token": order.id}

    # when
    response = api_client.post_graphql(QUERY_ORDER_BY_TOKEN_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_order_by_token_as_customer(user_api_client, order):
    # given
    order.user = user_api_client.user
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "metadata"])
    variables = {"token": order.id}

    # when
    response = user_api_client.post_graphql(QUERY_ORDER_BY_TOKEN_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_order_by_token_as_staff(
    staff_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "metadata"])
    variables = {"token": order.id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_BY_TOKEN_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_order_by_token_as_app(
    app_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "metadata"])
    variables = {"token": order.id}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_BY_TOKEN_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_ORDER_PUBLIC_META = """
    query orderMeta($id: ID!){
        order(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_order_as_anonymous_user(api_client, order):
    # given
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = api_client.post_graphql(QUERY_ORDER_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_order_as_customer(user_api_client, order):
    # given
    order.user = user_api_client.user
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_ORDER_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_order_as_staff(
    staff_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_order_as_app(
    app_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_DRAFT_ORDER_PUBLIC_META = """
    query draftOrderMeta($id: ID!){
        order(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_draft_order_as_anonymous_user(api_client, draft_order):
    # given
    draft_order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    draft_order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = api_client.post_graphql(QUERY_DRAFT_ORDER_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_draft_order_as_customer(user_api_client, draft_order):
    # given
    draft_order.user = user_api_client.user
    draft_order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    draft_order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_DRAFT_ORDER_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_draft_order_as_staff(
    staff_api_client, draft_order, customer_user, permission_manage_orders
):
    # given
    draft_order.user = customer_user
    draft_order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    draft_order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDER_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_draft_order_as_app(
    app_api_client, draft_order, customer_user, permission_manage_orders
):
    # given
    draft_order.user = customer_user
    draft_order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    draft_order.save(update_fields=["user", "metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_FULFILLMENT_PUBLIC_META = """
    query fulfillmentMeta($token: UUID!){
        orderByToken(token: $token){
            fulfillments{
                metadata{
                    key
                    value
                }
          }
        }
    }
"""


def test_query_public_meta_for_fulfillment_as_anonymous_user(
    api_client, fulfilled_order
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["metadata"])
    variables = {"token": fulfilled_order.id}

    # when
    response = api_client.post_graphql(QUERY_FULFILLMENT_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["fulfillments"][0]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_fulfillment_as_customer(
    user_api_client, fulfilled_order
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["metadata"])
    fulfilled_order.user = user_api_client.user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.id}

    # when
    response = user_api_client.post_graphql(QUERY_FULFILLMENT_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["fulfillments"][0]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_fulfillment_as_staff(
    staff_api_client, fulfilled_order, customer_user, permission_manage_orders
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["metadata"])
    fulfilled_order.user = customer_user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_FULFILLMENT_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["fulfillments"][0]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_fulfillment_as_app(
    app_api_client, fulfilled_order, customer_user, permission_manage_orders
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["metadata"])
    fulfilled_order.user = customer_user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.id}

    # when
    response = app_api_client.post_graphql(
        QUERY_FULFILLMENT_PUBLIC_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["fulfillments"][0]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_ATTRIBUTE_PUBLIC_META = """
    query attributeMeta($id: ID!){
        attribute(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_attribute_as_anonymous_user(api_client, color_attribute):
    # given
    color_attribute.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    color_attribute.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = api_client.post_graphql(QUERY_ATTRIBUTE_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["attribute"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_attribute_as_customer(user_api_client, color_attribute):
    # given
    color_attribute.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    color_attribute.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_ATTRIBUTE_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["attribute"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_attribute_as_staff(
    staff_api_client, color_attribute, permission_manage_products
):
    # given
    color_attribute.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    color_attribute.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ATTRIBUTE_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["attribute"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_attribute_as_app(
    app_api_client, color_attribute, permission_manage_products
):
    # given
    color_attribute.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    color_attribute.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ATTRIBUTE_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["attribute"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_CATEGORY_PUBLIC_META = """
    query categoryMeta($id: ID!){
        category(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_category_as_anonymous_user(api_client, category):
    # given
    category.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    category.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = api_client.post_graphql(QUERY_CATEGORY_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["category"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_category_as_customer(user_api_client, category):
    # given
    category.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    category.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_CATEGORY_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["category"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_category_as_staff(
    staff_api_client, category, permission_manage_products
):
    # given
    category.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    category.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CATEGORY_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["category"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_category_as_app(
    app_api_client, category, permission_manage_products
):
    # given
    category.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    category.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_CATEGORY_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["category"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_COLLECTION_PUBLIC_META = """
    query collectionMeta($id: ID!, $channel: String) {
        collection(id: $id, channel: $channel) {
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_collection_as_anonymous_user(
    api_client, published_collection, channel_USD
):
    # given
    collection = published_collection
    collection.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    collection.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Collection", collection.pk),
        "channel": channel_USD.slug,
    }
    # when
    response = api_client.post_graphql(QUERY_COLLECTION_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["collection"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_collection_as_customer(
    user_api_client, published_collection, channel_USD
):
    # given
    collection = published_collection
    collection.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    collection.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Collection", collection.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_COLLECTION_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["collection"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_collection_as_staff(
    staff_api_client, published_collection, permission_manage_products, channel_USD
):
    # given
    collection = published_collection
    collection.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    collection.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Collection", collection.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_COLLECTION_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["collection"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_collection_as_app(
    app_api_client, published_collection, permission_manage_products, channel_USD
):
    # given
    collection = published_collection
    collection.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    collection.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Collection", collection.pk),
        "channel": channel_USD.slug,
    }
    # when
    response = app_api_client.post_graphql(
        QUERY_COLLECTION_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["collection"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_DIGITAL_CONTENT_PUBLIC_META = """
    query digitalContentMeta($id: ID!){
        digitalContent(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_digital_content_as_anonymous_user(
    api_client, digital_content
):
    # given
    variables = {"id": graphene.Node.to_global_id("DigitalContent", digital_content.pk)}

    # when
    response = api_client.post_graphql(QUERY_DIGITAL_CONTENT_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_digital_content_as_customer(
    user_api_client, digital_content
):
    # given
    digital_content.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    digital_content.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("DigitalContent", digital_content.pk)}

    # when
    response = user_api_client.post_graphql(
        QUERY_DIGITAL_CONTENT_PUBLIC_META, variables
    )

    # then
    assert_no_permission(response)


def test_query_public_meta_for_digital_content_as_staff(
    staff_api_client, digital_content, permission_manage_products
):
    # given
    digital_content.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    digital_content.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("DigitalContent", digital_content.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_DIGITAL_CONTENT_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["digitalContent"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_digital_content_as_app(
    app_api_client, digital_content, permission_manage_products
):
    # given
    digital_content.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    digital_content.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("DigitalContent", digital_content.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_DIGITAL_CONTENT_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["digitalContent"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_TRANSACTION_ITEM_PUBLIC_META = """
query transactionItemMeta($id: ID!){
  order(id: $id){
    transactions{
      metadata{
        key
        value
      }
    }
  }
}
"""


def execute_query_public_metadata_for_transaction_item(
    client: ApiClient, order: Order, permissions: List[Permission] = None
):
    return execute_query(
        QUERY_TRANSACTION_ITEM_PUBLIC_META, client, order, "Order", permissions
    )


def assert_transaction_item_contains_metadata(response):
    content = get_graphql_content(response)
    metadata = content["data"]["order"]["transactions"][0]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_transaction_item_as_customer(
    user_api_client, order, permission_manage_orders
):
    # given
    order.payment_transactions.create(metadata={PUBLIC_KEY: PUBLIC_VALUE})
    order.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["metadata"])

    # when
    response = execute_query_public_metadata_for_transaction_item(
        user_api_client,
        order,
        permissions=[],
    )

    # then
    assert_no_permission(response)


def test_query_public_meta_for_transaction_item_as_staff_with_permission(
    staff_api_client,
    order_with_lines,
    permission_manage_orders,
    permission_manage_payments,
):
    # given
    order_with_lines.payment_transactions.create(metadata={PUBLIC_KEY: PUBLIC_VALUE})

    # when
    response = execute_query_public_metadata_for_transaction_item(
        staff_api_client,
        order_with_lines,
        permissions=[permission_manage_orders, permission_manage_payments],
    )

    # then
    assert_transaction_item_contains_metadata(response)


def test_query_public_meta_for_transaction_item_as_staff_without_permission(
    staff_api_client, order
):
    # given
    order.payment_transactions.create(metadata={PUBLIC_KEY: PUBLIC_VALUE})

    # when
    response = execute_query_public_metadata_for_transaction_item(
        staff_api_client, order
    )

    # then
    assert_no_permission(response)


def test_query_public_meta_for_transaction_item_as_app_with_permission(
    app_api_client,
    order,
    permission_manage_orders,
    permission_manage_payments,
):
    order.payment_transactions.create(metadata={PUBLIC_KEY: PUBLIC_VALUE})

    # when
    response = execute_query_public_metadata_for_transaction_item(
        app_api_client,
        order,
        permissions=[permission_manage_payments, permission_manage_orders],
    )

    # then
    assert_transaction_item_contains_metadata(response)


def test_query_public_meta_for_transaction_item_as_app_without_permission(
    app_api_client, order
):
    # when
    response = execute_query_public_metadata_for_transaction_item(app_api_client, order)

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


QUERY_PRODUCT_PUBLIC_META = """
    query productsMeta($id: ID!, $channel: String){
        product(id: $id, channel: $channel){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_product_as_anonymous_user(
    api_client, product, channel_USD
):
    # given
    product.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    product.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(QUERY_PRODUCT_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["product"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_product_as_customer(
    user_api_client, product, channel_USD
):
    # given
    product.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    product.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_PRODUCT_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["product"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_product_as_staff(
    staff_api_client, product, permission_manage_products
):
    # given
    product.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    product.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["product"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_product_as_app(
    app_api_client, product, permission_manage_products
):
    # given
    product.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    product.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_PRODUCT_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["product"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_PRODUCT_TYPE_PUBLIC_META = """
    query productTypeMeta($id: ID!){
        productType(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_product_type_as_anonymous_user(api_client, product_type):
    # given
    product_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    product_type.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.pk)}

    # when
    response = api_client.post_graphql(QUERY_PRODUCT_TYPE_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productType"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_product_type_as_customer(user_api_client, product_type):
    # given
    product_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    product_type.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_PRODUCT_TYPE_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productType"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_product_type_as_staff(
    staff_api_client, product_type, permission_manage_products
):
    # given
    product_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    product_type.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_TYPE_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productType"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_product_type_as_app(
    app_api_client, product_type, permission_manage_products
):
    # given
    product_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    product_type.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_PRODUCT_TYPE_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productType"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_PRODUCT_VARIANT_PUBLIC_META = """
    query productVariantMeta($id: ID!, $channel: String){
        productVariant(id: $id, channel: $channel){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_product_variant_as_anonymous_user(
    api_client, variant, channel_USD
):
    # given
    variant.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    variant.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(QUERY_PRODUCT_VARIANT_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productVariant"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_product_variant_as_customer(
    user_api_client, variant, channel_USD
):
    # given
    variant.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    variant.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_PUBLIC_META, variables
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productVariant"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_product_variant_as_staff(
    staff_api_client, variant, permission_manage_products
):
    # given
    variant.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    variant.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productVariant"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_product_variant_as_app(
    app_api_client, variant, permission_manage_products
):
    # given
    variant.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    variant.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
    }

    # when
    response = app_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productVariant"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_APP_PUBLIC_META = """
    query appMeta($id: ID!){
        app(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_app_as_anonymous_user(api_client, app):
    # given
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = api_client.post_graphql(QUERY_APP_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_app_as_customer(user_api_client, app):
    # given
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_APP_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_app_as_staff(
    staff_api_client, app, permission_manage_apps
):
    # given
    app.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    app.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_PUBLIC_META,
        variables,
        [permission_manage_apps],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["app"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_app_as_app(app_api_client, app, permission_manage_apps):
    # given
    app.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    app.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_PUBLIC_META,
        variables,
        [permission_manage_apps],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["app"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_PAGE_TYPE_PUBLIC_META = """
    query pageTypeMeta($id: ID!){
        pageType(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_page_type_as_anonymous_user(api_client, page_type):
    # given
    page_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    page_type.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = api_client.post_graphql(QUERY_PAGE_TYPE_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["pageType"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_page_type_as_customer(user_api_client, page_type):
    # given
    page_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    page_type.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_PAGE_TYPE_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["pageType"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_page_type_as_staff(
    staff_api_client, page_type, permission_manage_products
):
    # given
    page_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    page_type.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGE_TYPE_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["pageType"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_page_type_as_app(
    app_api_client, page_type, permission_manage_products
):
    # given
    page_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    page_type.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_PAGE_TYPE_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["pageType"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_GIFT_CARD_PUBLIC_META = """
    query giftCardMeta($id: ID!){
        giftCard(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_gift_card_as_anonymous_user(api_client, gift_card):
    # given
    gift_card.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    gift_card.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = api_client.post_graphql(QUERY_GIFT_CARD_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_gift_card_as_customer(user_api_client, gift_card):
    # given
    gift_card.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    gift_card.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_GIFT_CARD_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_gift_card_as_staff(
    staff_api_client, gift_card, permission_manage_gift_card
):
    # given
    gift_card.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    gift_card.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_PUBLIC_META,
        variables,
        [permission_manage_gift_card],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["giftCard"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_gift_card_as_app(
    app_api_client, gift_card, permission_manage_gift_card
):
    # given
    gift_card.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    gift_card.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_GIFT_CARD_PUBLIC_META,
        variables,
        [permission_manage_gift_card],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["giftCard"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_SELF_PRIVATE_META = """
    {
        me{
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_me_as_customer(user_api_client):
    # given

    # when
    response = user_api_client.post_graphql(QUERY_SELF_PRIVATE_META)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_me_as_staff_with_manage_customer(
    staff_api_client, permission_manage_users
):
    # given

    # when
    response = staff_api_client.post_graphql(
        QUERY_SELF_PRIVATE_META, None, [permission_manage_users]
    )

    # then
    assert_no_permission(response)


def test_query_private_meta_for_me_as_staff_with_manage_staff(
    staff_api_client, permission_manage_staff
):
    # given
    me = staff_api_client.user
    me.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    me.save(update_fields=["private_metadata"])

    # when
    response = staff_api_client.post_graphql(
        QUERY_SELF_PRIVATE_META, None, [permission_manage_staff]
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["me"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_USER_PRIVATE_META = """
    query userMeta($id: ID!){
        user(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_customer_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    customer_user.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_USER_PRIVATE_META, variables, [permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["user"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    customer_user.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_USER_PRIVATE_META, variables, [permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["user"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_staff_as_other_staff(
    staff_api_client, permission_manage_staff, admin_user
):
    # given
    admin_user.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    admin_user.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("User", admin_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_USER_PRIVATE_META, variables, [permission_manage_staff]
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["user"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_CHECKOUT_PRIVATE_META = """
    query checkoutMeta($token: UUID!){
        checkout(token: $token){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_checkout_as_anonymous_user(api_client, checkout):
    # given
    variables = {"token": checkout.pk}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_other_customer_checkout_as_anonymous_user(
    api_client, checkout, customer_user
):
    # given
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"token": checkout.pk}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_PRIVATE_META, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkout"]


def test_query_private_meta_for_checkout_as_customer(user_api_client, checkout):
    # given
    checkout.user = user_api_client.user
    checkout.save(update_fields=["user"])
    variables = {"token": checkout.pk}

    # when
    response = user_api_client.post_graphql(QUERY_CHECKOUT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_checkout_as_staff(
    staff_api_client, checkout, customer_user, permission_manage_checkouts
):
    # given
    checkout.user = customer_user
    checkout.metadata_storage.store_value_in_private_metadata(
        {PRIVATE_KEY: PRIVATE_VALUE}
    )
    checkout.save(update_fields=["user"])
    checkout.metadata_storage.save(update_fields=["private_metadata"])
    variables = {"token": checkout.pk}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CHECKOUT_PRIVATE_META,
        variables,
        [permission_manage_checkouts],
        check_no_permissions=False,  # Remove after fix #5245
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["checkout"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_checkout_as_app(
    app_api_client, checkout, customer_user, permission_manage_checkouts
):
    # given
    checkout.user = customer_user
    checkout.metadata_storage.store_value_in_private_metadata(
        {PRIVATE_KEY: PRIVATE_VALUE}
    )
    checkout.save(update_fields=["user"])
    checkout.metadata_storage.save(update_fields=["private_metadata"])
    variables = {"token": checkout.pk}

    # when
    response = app_api_client.post_graphql(
        QUERY_CHECKOUT_PRIVATE_META,
        variables,
        [permission_manage_checkouts],
        check_no_permissions=False,  # Remove after fix #5245
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["checkout"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_ORDER_BY_TOKEN_PRIVATE_META = """
    query orderMeta($token: UUID!){
        orderByToken(token: $token){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_order_by_token_as_anonymous_user(api_client, order):
    # given
    variables = {"token": order.id}

    # when
    response = api_client.post_graphql(QUERY_ORDER_BY_TOKEN_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_order_by_token_as_customer(user_api_client, order):
    # given
    order.user = user_api_client.user
    order.save(update_fields=["user"])
    variables = {"token": order.id}

    # when
    response = user_api_client.post_graphql(
        QUERY_ORDER_BY_TOKEN_PRIVATE_META, variables
    )

    # then
    assert_no_permission(response)


def test_query_private_meta_for_order_by_token_as_staff(
    staff_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["user", "private_metadata"])
    variables = {"token": order.id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_BY_TOKEN_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_order_by_token_as_app(
    app_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["user", "private_metadata"])
    variables = {"token": order.id}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_BY_TOKEN_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_ORDER_PRIVATE_META = """
    query orderMeta($id: ID!){
        order(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_order_as_anonymous_user(api_client, order):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = api_client.post_graphql(QUERY_ORDER_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_order_as_customer(user_api_client, order):
    # given
    order.user = user_api_client.user
    order.save(update_fields=["user"])
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_ORDER_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_order_as_staff(
    staff_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["user", "private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_order_as_app(
    app_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["user", "private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_DRAFT_ORDER_PRIVATE_META = """
    query draftOrderMeta($id: ID!){
        order(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_draft_order_as_anonymous_user(api_client, draft_order):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = api_client.post_graphql(QUERY_DRAFT_ORDER_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_draft_order_as_customer(user_api_client, draft_order):
    # given
    draft_order.user = user_api_client.user
    draft_order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    draft_order.save(update_fields=["user", "private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_DRAFT_ORDER_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_draft_order_as_staff(
    staff_api_client, draft_order, customer_user, permission_manage_orders
):
    # given
    draft_order.user = customer_user
    draft_order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    draft_order.save(update_fields=["user", "private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDER_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_draft_order_as_app(
    app_api_client, draft_order, customer_user, permission_manage_orders
):
    # given
    draft_order.user = customer_user
    draft_order.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    draft_order.save(update_fields=["user", "private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["order"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_FULFILLMENT_PRIVATE_META = """
    query fulfillmentMeta($token: UUID!){
        orderByToken(token: $token){
            fulfillments{
                privateMetadata{
                    key
                    value
                }
          }
        }
    }
"""


def test_query_private_meta_for_fulfillment_as_anonymous_user(
    api_client, fulfilled_order
):
    # given
    variables = {"token": fulfilled_order.id}

    # when
    response = api_client.post_graphql(QUERY_FULFILLMENT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_fulfillment_as_customer(
    user_api_client, fulfilled_order
):
    # given
    fulfilled_order.user = user_api_client.user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.id}

    # when
    response = user_api_client.post_graphql(QUERY_FULFILLMENT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_fulfillment_as_staff(
    staff_api_client, fulfilled_order, customer_user, permission_manage_orders
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    fulfillment.save(update_fields=["private_metadata"])
    fulfilled_order.user = customer_user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_FULFILLMENT_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["fulfillments"][0]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_fulfillment_as_app(
    app_api_client, fulfilled_order, customer_user, permission_manage_orders
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    fulfillment.save(update_fields=["private_metadata"])
    fulfilled_order.user = customer_user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.id}

    # when
    response = app_api_client.post_graphql(
        QUERY_FULFILLMENT_PRIVATE_META,
        variables,
        [permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["orderByToken"]["fulfillments"][0]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_ATTRIBUTE_PRIVATE_META = """
    query attributeMeta($id: ID!){
        attribute(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_attribute_as_anonymous_user(
    api_client, color_attribute
):
    # given
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = api_client.post_graphql(QUERY_ATTRIBUTE_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_attribute_as_customer(user_api_client, color_attribute):
    # given
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_ATTRIBUTE_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_attribute_as_staff(
    staff_api_client, color_attribute, permission_manage_product_types_and_attributes
):
    # given
    color_attribute.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    color_attribute.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ATTRIBUTE_PRIVATE_META,
        variables,
        [permission_manage_product_types_and_attributes],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["attribute"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_attribute_as_app(
    app_api_client, color_attribute, permission_manage_product_types_and_attributes
):
    # given
    color_attribute.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    color_attribute.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ATTRIBUTE_PRIVATE_META,
        variables,
        [permission_manage_product_types_and_attributes],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["attribute"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_CATEGORY_PRIVATE_META = """
    query categoryMeta($id: ID!){
        category(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_category_as_anonymous_user(api_client, category):
    # given
    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = api_client.post_graphql(QUERY_CATEGORY_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_category_as_customer(user_api_client, category):
    # given
    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_CATEGORY_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_category_as_staff(
    staff_api_client, category, permission_manage_products
):
    # given
    category.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    category.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CATEGORY_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["category"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_category_as_app(
    app_api_client, category, permission_manage_products
):
    # given
    category.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    category.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_CATEGORY_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["category"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_COLLECTION_PRIVATE_META = """
    query collectionMeta($id: ID!, $channel: String){
        collection(id: $id, channel: $channel){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_collection_as_anonymous_user(
    api_client, published_collection, channel_USD
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(QUERY_COLLECTION_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_collection_as_customer(
    user_api_client, published_collection, channel_USD
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_COLLECTION_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_collection_as_staff(
    staff_api_client, published_collection, permission_manage_products, channel_USD
):
    # given
    collection = published_collection
    collection.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    collection.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_COLLECTION_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["collection"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_collection_as_app(
    app_api_client, published_collection, permission_manage_products, channel_USD
):
    # given
    collection = published_collection
    collection.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    collection.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Collection", collection.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(
        QUERY_COLLECTION_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["collection"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_DIGITAL_CONTENT_PRIVATE_META = """
    query digitalContentMeta($id: ID!){
        digitalContent(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_digital_content_as_anonymous_user(
    api_client, digital_content
):
    # given
    variables = {"id": graphene.Node.to_global_id("DigitalContent", digital_content.pk)}

    # when
    response = api_client.post_graphql(QUERY_DIGITAL_CONTENT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_digital_content_as_customer(
    user_api_client, digital_content
):
    # given
    digital_content.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    digital_content.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("DigitalContent", digital_content.pk)}

    # when
    response = user_api_client.post_graphql(
        QUERY_DIGITAL_CONTENT_PRIVATE_META, variables
    )

    # then
    assert_no_permission(response)


def test_query_private_meta_for_digital_content_as_staff(
    staff_api_client, digital_content, permission_manage_products
):
    # given
    digital_content.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    digital_content.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("DigitalContent", digital_content.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_DIGITAL_CONTENT_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["digitalContent"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_digital_content_as_app(
    app_api_client, digital_content, permission_manage_products
):
    # given
    digital_content.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    digital_content.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("DigitalContent", digital_content.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_DIGITAL_CONTENT_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["digitalContent"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_TRANSACTION_ITEM_PRIVATE_META = """
query transactionItemMeta($id: ID!){
  order(id: $id){
    transactions{
      privateMetadata{
        key
        value
      }
    }
  }
}
"""


def execute_query_private_metadata_for_transaction_item(
    client: ApiClient, order: Order, permissions: List[Permission] = None
):
    return execute_query(
        QUERY_TRANSACTION_ITEM_PRIVATE_META, client, order, "Order", permissions
    )


def assert_transaction_item_contains_private_metadata(response):
    content = get_graphql_content(response)
    metadata = content["data"]["order"]["transactions"][0]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_transaction_item_as_customer(
    user_api_client, order, permission_manage_orders
):
    # given
    order.payment_transactions.create(private_metadata={PRIVATE_KEY: PRIVATE_VALUE})

    # when
    response = execute_query_public_metadata_for_transaction_item(
        user_api_client,
        order,
        permissions=[],
    )

    # then
    assert_no_permission(response)


#


def test_query_private_meta_for_transaction_item_as_staff_with_permission(
    staff_api_client,
    order_with_lines,
    permission_manage_orders,
    permission_manage_payments,
):
    # given
    order_with_lines.payment_transactions.create(
        private_metadata={PRIVATE_KEY: PRIVATE_VALUE}
    )

    # when
    response = execute_query_private_metadata_for_transaction_item(
        staff_api_client,
        order_with_lines,
        permissions=[permission_manage_orders, permission_manage_payments],
    )

    # then
    assert_transaction_item_contains_private_metadata(response)


def test_query_private_meta_for_transaction_item_as_staff_without_permission(
    staff_api_client, order
):
    # given
    order.payment_transactions.create(private_metadata={PRIVATE_KEY: PRIVATE_VALUE})

    # when
    response = execute_query_private_metadata_for_transaction_item(
        staff_api_client, order
    )

    # then
    assert_no_permission(response)


def test_query_private_meta_for_transaction_item_as_app_with_permission(
    app_api_client,
    order,
    permission_manage_orders,
    permission_manage_payments,
):
    order.payment_transactions.create(private_metadata={PRIVATE_KEY: PRIVATE_VALUE})

    # when
    response = execute_query_private_metadata_for_transaction_item(
        app_api_client,
        order,
        permissions=[permission_manage_payments, permission_manage_orders],
    )

    # then
    assert_transaction_item_contains_private_metadata(response)


def test_query_private_meta_for_transaction_item_as_app_without_permission(
    app_api_client, order
):
    # when
    response = execute_query_private_metadata_for_transaction_item(
        app_api_client, order
    )

    # then
    assert_no_permission(response)


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


QUERY_PRODUCT_PRIVATE_META = """
    query productsMeta($id: ID!, $channel: String){
        product(id: $id, channel: $channel){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_product_as_anonymous_user(
    api_client, product, channel_USD
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(QUERY_PRODUCT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_product_as_customer(
    user_api_client, product, channel_USD
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_PRODUCT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_product_as_staff(
    staff_api_client, product, permission_manage_products
):
    # given
    product.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    product.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["product"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_product_as_app(
    app_api_client, product, permission_manage_products
):
    # given
    product.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    product.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
    }

    # when
    response = app_api_client.post_graphql(
        QUERY_PRODUCT_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["product"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_PRODUCT_TYPE_PRIVATE_META = """
    query productTypeMeta($id: ID!){
        productType(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_product_type_as_anonymous_user(
    api_client, product_type
):
    # given
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.pk)}

    # when
    response = api_client.post_graphql(QUERY_PRODUCT_TYPE_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_product_type_as_customer(user_api_client, product_type):
    # given
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_PRODUCT_TYPE_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_product_type_as_staff(
    staff_api_client, product_type, permission_manage_product_types_and_attributes
):
    # given
    product_type.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    product_type.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_TYPE_PRIVATE_META,
        variables,
        [permission_manage_product_types_and_attributes],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productType"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_product_type_as_app(
    app_api_client, product_type, permission_manage_product_types_and_attributes
):
    # given
    product_type.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    product_type.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_PRODUCT_TYPE_PRIVATE_META,
        variables,
        [permission_manage_product_types_and_attributes],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productType"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_PRODUCT_VARIANT_PRIVATE_META = """
    query productVariantMeta($id: ID!, $channel: String){
        productVariant(id: $id, channel: $channel){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_product_variant_as_anonymous_user(
    api_client, variant, channel_USD
):
    # given
    variant.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    variant.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(QUERY_PRODUCT_VARIANT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_product_variant_as_customer(
    user_api_client, variant, channel_USD
):
    # given
    variant.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    variant.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_PRIVATE_META, variables
    )

    # then
    assert_no_permission(response)


def test_query_private_meta_for_product_variant_as_staff(
    staff_api_client, variant, permission_manage_products
):
    # given
    variant.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    variant.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productVariant"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_product_variant_as_app(
    app_api_client, variant, permission_manage_products
):
    # given
    variant.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    variant.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
    }

    # when
    response = app_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productVariant"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_APP_PRIVATE_META = """
    query appMeta($id: ID!){
        app(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_app_as_anonymous_user(api_client, app):
    # given
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = api_client.post_graphql(QUERY_APP_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_app_as_customer(user_api_client, app):
    # given
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_APP_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_app_as_staff(
    staff_api_client, app, permission_manage_apps
):
    # given
    app.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    app.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_PRIVATE_META,
        variables,
        [permission_manage_apps],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["app"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_app_as_app(app_api_client, app, permission_manage_apps):
    # given
    app.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    app.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("App", app.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_APP_PRIVATE_META,
        variables,
        [permission_manage_apps],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["app"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_PAGE_TYPE_PRIVATE_META = """
    query pageTypeMeta($id: ID!){
        pageType(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_page_type_as_anonymous_user(api_client, page_type):
    # given
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = api_client.post_graphql(QUERY_PAGE_TYPE_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_page_type_as_customer(user_api_client, page_type):
    # given
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_PAGE_TYPE_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_page_type_as_staff(
    staff_api_client, page_type, permission_manage_page_types_and_attributes
):
    # given
    page_type.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    page_type.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGE_TYPE_PRIVATE_META,
        variables,
        [permission_manage_page_types_and_attributes],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["pageType"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_page_type_as_app(
    app_api_client, page_type, permission_manage_page_types_and_attributes
):
    # given
    page_type.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    page_type.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("PageType", page_type.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_PAGE_TYPE_PRIVATE_META,
        variables,
        [permission_manage_page_types_and_attributes],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["pageType"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_WAREHOUSE_PUBLIC_META = """
    query warehouseMeta($id: ID!){
         warehouse(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_warehouse_as_anonymous_user(api_client, warehouse):
    # given
    warehouse.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    warehouse.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Warehouse", warehouse.pk),
    }

    # when
    response = api_client.post_graphql(QUERY_WAREHOUSE_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_warehouse_as_customer(user_api_client, warehouse):
    # given
    warehouse.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    warehouse.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Warehouse", warehouse.pk),
    }

    # when
    response = user_api_client.post_graphql(QUERY_WAREHOUSE_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_warehouse_as_staff(
    staff_api_client, warehouse, permission_manage_products
):
    # given
    warehouse.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    warehouse.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Warehouse", warehouse.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSE_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["warehouse"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_warehouse_as_app(
    app_api_client, warehouse, permission_manage_products
):
    # given
    warehouse.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    warehouse.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Warehouse", warehouse.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_WAREHOUSE_PUBLIC_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["warehouse"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_WAREHOUSE_PRIVATE_META = """
    query warehouseMeta($id: ID!){
        warehouse(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_warehouse_as_anonymous_user(api_client, warehouse):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Warehouse", warehouse.pk),
    }

    # when
    response = api_client.post_graphql(QUERY_WAREHOUSE_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_warehouse_as_customer(user_api_client, warehouse):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Warehouse", warehouse.pk),
    }

    # when
    response = user_api_client.post_graphql(QUERY_WAREHOUSE_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_warehouse_as_staff(
    staff_api_client, warehouse, permission_manage_products
):
    # given
    warehouse.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    warehouse.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Warehouse", warehouse.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSE_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["warehouse"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_warehouse_as_app(
    app_api_client, warehouse, permission_manage_products
):
    # given
    warehouse.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    warehouse.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Warehouse", warehouse.pk),
    }

    # when
    response = app_api_client.post_graphql(
        QUERY_WAREHOUSE_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["warehouse"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_VOUCHER_PUBLIC_META = """
    query voucherMeta($id: ID!){
         voucher(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_voucher_as_anonymous_user(api_client, voucher):
    # given
    voucher.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    voucher.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
    }

    # when
    response = api_client.post_graphql(QUERY_VOUCHER_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_voucher_as_customer(user_api_client, voucher):
    # given
    voucher.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    voucher.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
    }

    # when
    response = user_api_client.post_graphql(QUERY_VOUCHER_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_voucher_as_staff(
    staff_api_client, voucher, permission_manage_discounts
):
    # given
    voucher.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    voucher.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_PUBLIC_META,
        variables,
        [permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["voucher"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_voucher_as_app(
    app_api_client, voucher, permission_manage_discounts
):
    # given
    voucher.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    voucher.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_VOUCHER_PUBLIC_META,
        variables,
        [permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["voucher"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_VOUCHER_PRIVATE_META = """
    query voucherMeta($id: ID!){
        voucher(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_voucher_as_anonymous_user(api_client, voucher):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
    }

    # when
    response = api_client.post_graphql(QUERY_VOUCHER_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_voucher_as_customer(user_api_client, voucher):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
    }

    # when
    response = user_api_client.post_graphql(QUERY_VOUCHER_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_voucher_as_staff(
    staff_api_client, voucher, permission_manage_discounts
):
    # given
    voucher.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    voucher.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_PRIVATE_META,
        variables,
        [permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["voucher"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_voucher_as_app(
    app_api_client, voucher, permission_manage_discounts
):
    # given
    voucher.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    voucher.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
    }

    # when
    response = app_api_client.post_graphql(
        QUERY_VOUCHER_PRIVATE_META,
        variables,
        [permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["voucher"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_SALE_PUBLIC_META = """
    query saleMeta($id: ID!){
         sale(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_sale_as_anonymous_user(api_client, sale):
    # given
    sale.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    sale.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.pk),
    }

    # when
    response = api_client.post_graphql(QUERY_SALE_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_sale_as_customer(user_api_client, sale):
    # given
    sale.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    sale.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.pk),
    }

    # when
    response = user_api_client.post_graphql(QUERY_SALE_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_sale_as_staff(
    staff_api_client, sale, permission_manage_discounts
):
    # given
    sale.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    sale.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Sale", sale.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_SALE_PUBLIC_META,
        variables,
        [permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["sale"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_sale_as_app(
    app_api_client, sale, permission_manage_discounts
):
    # given
    sale.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    sale.save(update_fields=["metadata"])
    variables = {"id": graphene.Node.to_global_id("Sale", sale.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_SALE_PUBLIC_META,
        variables,
        [permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["sale"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


QUERY_SALE_PRIVATE_META = """
    query saleMeta($id: ID!){
        sale(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_sale_as_anonymous_user(api_client, sale):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.pk),
    }

    # when
    response = api_client.post_graphql(QUERY_SALE_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_sale_as_customer(user_api_client, sale):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.pk),
    }

    # when
    response = user_api_client.post_graphql(QUERY_SALE_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_sale_as_staff(
    staff_api_client, sale, permission_manage_discounts
):
    # given
    sale.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    sale.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Sale", sale.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_SALE_PRIVATE_META,
        variables,
        [permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["sale"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_sale_as_app(
    app_api_client, sale, permission_manage_discounts
):
    # given
    sale.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    sale.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.pk),
    }

    # when
    response = app_api_client.post_graphql(
        QUERY_SALE_PRIVATE_META,
        variables,
        [permission_manage_discounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["sale"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_GIFT_CARD_PRIVATE_META = """
    query giftCardMeta($id: ID!){
        giftCard(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_gift_card_as_anonymous_user(api_client, gift_card):
    # given
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
    }

    # when
    response = api_client.post_graphql(QUERY_GIFT_CARD_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_gift_card_as_customer(user_api_client, gift_card):
    # given
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
    }

    # when
    response = user_api_client.post_graphql(QUERY_GIFT_CARD_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_gift_card_as_staff(
    staff_api_client, gift_card, permission_manage_gift_card
):
    # given
    gift_card.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    gift_card.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_PRIVATE_META,
        variables,
        [permission_manage_gift_card],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["giftCard"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_gift_card_as_app(
    app_api_client, gift_card, permission_manage_gift_card
):
    # given
    gift_card.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    gift_card.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
    }

    # when
    response = app_api_client.post_graphql(
        QUERY_GIFT_CARD_PRIVATE_META,
        variables,
        [permission_manage_gift_card],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["giftCard"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE
