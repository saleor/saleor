import base64

import graphene

from saleor.core.error_codes import MetadataErrorCode
from saleor.core.models import ModelWithMetadata
from tests.api.utils import assert_no_permission, get_graphql_content

PRIVATE_KEY = "private_key"
PRIVATE_VALUE = "private_vale"

PUBLIC_KEY = "key"
PUBLIC_VALUE = "value"


QUERY_SELF_PUBLIC_META = """
    {
        me{
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_me_as_customer(user_api_client):
    # given
    me = user_api_client.user
    me.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    me.save(update_fields=["meta"])

    # when
    response = user_api_client.post_graphql(QUERY_SELF_PUBLIC_META)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["me"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_me_as_staff(staff_api_client):
    # given
    me = staff_api_client.user
    me.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    me.save(update_fields=["meta"])

    # when
    response = staff_api_client.post_graphql(QUERY_SELF_PUBLIC_META)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["me"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


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
    customer_user.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    customer_user.save(update_fields=["meta"])
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


def test_query_public_meta_for_customer_as_service_account(
    service_account_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    customer_user.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = service_account_api_client.post_graphql(
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
    admin_user.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    admin_user.save(update_fields=["meta"])
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


def test_query_public_meta_for_staff_as_service_account(
    service_account_api_client, permission_manage_staff, admin_user
):
    # given
    admin_user.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    admin_user.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("User", admin_user.pk)}

    # when
    response = service_account_api_client.post_graphql(
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
    checkout.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.save(update_fields=["meta"])
    variables = {"token": checkout.pk}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["checkout"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


# TODO: Restore after #5245
# def test_query_public_meta_for_other_customer_checkout_as_anonymous_user(
#     api_client, checkout, customer_user
# ):
#     # given
#     checkout.user = customer_user
#     checkout.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
#     checkout.save(update_fields=["user", "meta"])
#     variables = {"token": checkout.pk}

#     # when
#     response = api_client.post_graphql(QUERY_CHECKOUT_PUBLIC_META, variables)

#     # then
#     assert_no_permission(response)


def test_query_public_meta_for_checkout_as_customer(user_api_client, checkout):
    # given
    checkout.user = user_api_client.user
    checkout.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.save(update_fields=["user", "meta"])
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
    checkout.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.save(update_fields=["user", "meta"])
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


def test_query_public_meta_for_checkout_as_service_account(
    service_account_api_client, checkout, customer_user, permission_manage_checkouts
):
    # given
    checkout.user = customer_user
    checkout.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.save(update_fields=["user", "meta"])
    variables = {"token": checkout.pk}

    # when
    response = service_account_api_client.post_graphql(
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
    order.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["meta"])
    variables = {"token": order.token}

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
    order.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "meta"])
    variables = {"token": order.token}

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
    order.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "meta"])
    variables = {"token": order.token}

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


def test_query_public_meta_for_order_by_token_as_service_account(
    service_account_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "meta"])
    variables = {"token": order.token}

    # when
    response = service_account_api_client.post_graphql(
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
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = api_client.post_graphql(QUERY_ORDER_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_order_as_customer(user_api_client, order):
    # given
    order.user = user_api_client.user
    order.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "meta"])
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
    order.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["user", "meta"])
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


# TODO: Restore after #5251
# def test_query_public_meta_for_order_as_service_account(
#     service_account_api_client, order, customer_user, permission_manage_orders
# ):
#     # given
#     order.user = customer_user
#     order.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
#     order.save(update_fields=["user", "meta"])
#     variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

#     # when
#     response = service_account_api_client.post_graphql(
#         QUERY_ORDER_PUBLIC_META,
#         variables,
#         [permission_manage_orders],
#         check_no_permissions=False,
#     )
#     content = get_graphql_content(response)

#     # then
#     metadata = content["data"]["order"]["metadata"][0]
#     assert metadata["key"] == PUBLIC_KEY
#     assert metadata["value"] == PUBLIC_VALUE


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
    variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

    # when
    response = api_client.post_graphql(QUERY_DRAFT_ORDER_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


# TODO: Restore after #5252
# def test_query_public_meta_for_draft_order_as_customer(user_api_client, draft_order):
#     # given
#     draft_order.user = user_api_client.user
#     draft_order.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
#     draft_order.save(update_fields=["user", "meta"])
#     variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

#     # when
#     response = user_api_client.post_graphql(QUERY_DRAFT_ORDER_PUBLIC_META, variables)

#     # then
#     assert_no_permission(response)


def test_query_public_meta_for_draft_order_as_staff(
    staff_api_client, draft_order, customer_user, permission_manage_orders
):
    # given
    draft_order.user = customer_user
    draft_order.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    draft_order.save(update_fields=["user", "meta"])
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


# TODO: Restore after #5251
# def test_query_public_meta_for_draft_order_as_service_account(
#     service_account_api_client, draft_order, customer_user, permission_manage_orders
# ):
#     # given
#     draft_order.user = customer_user
#     draft_order.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
#     draft_order.save(update_fields=["user", "meta"])
#     variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

#     # when
#     response = service_account_api_client.post_graphql(
#         QUERY_ORDER_PUBLIC_META,
#         variables,
#         [permission_manage_orders],
#         check_no_permissions=False,
#     )
#     content = get_graphql_content(response)

#     # then
#     metadata = content["data"]["order"]["metadata"][0]
#     assert metadata["key"] == PUBLIC_KEY
#     assert metadata["value"] == PUBLIC_VALUE


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
    fulfillment.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["meta"])
    variables = {"token": fulfilled_order.token}

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
    fulfillment.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["meta"])
    fulfilled_order.user = user_api_client.user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.token}

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
    fulfillment.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["meta"])
    fulfilled_order.user = customer_user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.token}

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


def test_query_public_meta_for_fulfillment_as_service_account(
    service_account_api_client, fulfilled_order, customer_user, permission_manage_orders
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["meta"])
    fulfilled_order.user = customer_user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.token}

    # when
    response = service_account_api_client.post_graphql(
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
    color_attribute.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    color_attribute.save(update_fields=["meta"])
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
    color_attribute.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    color_attribute.save(update_fields=["meta"])
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
    color_attribute.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    color_attribute.save(update_fields=["meta"])
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


def test_query_public_meta_for_attribute_as_service_account(
    service_account_api_client, color_attribute, permission_manage_products
):
    # given
    color_attribute.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    color_attribute.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = service_account_api_client.post_graphql(
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
    category.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    category.save(update_fields=["meta"])
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
    category.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    category.save(update_fields=["meta"])
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
    category.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    category.save(update_fields=["meta"])
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


def test_query_public_meta_for_category_as_service_account(
    service_account_api_client, category, permission_manage_products
):
    # given
    category.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    category.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = service_account_api_client.post_graphql(
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
    query collectionMeta($id: ID!){
        collection(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_collection_as_anonymous_user(api_client, collection):
    # given
    collection.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    collection.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("Collection", collection.pk)}

    # when
    response = api_client.post_graphql(QUERY_COLLECTION_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["collection"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_collection_as_customer(user_api_client, collection):
    # given
    collection.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    collection.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("Collection", collection.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_COLLECTION_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["collection"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_collection_as_staff(
    staff_api_client, collection, permission_manage_products
):
    # given
    collection.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    collection.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("Collection", collection.pk)}

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


def test_query_public_meta_for_collection_as_service_account(
    service_account_api_client, collection, permission_manage_products
):
    # given
    collection.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    collection.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("Collection", collection.pk)}

    # when
    response = service_account_api_client.post_graphql(
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
    digital_content.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    digital_content.save(update_fields=["meta"])
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
    digital_content.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    digital_content.save(update_fields=["meta"])
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


def test_query_public_meta_for_digital_content_as_service_account(
    service_account_api_client, digital_content, permission_manage_products
):
    # given
    digital_content.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    digital_content.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("DigitalContent", digital_content.pk)}

    # when
    response = service_account_api_client.post_graphql(
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


QUERY_PRODUCT_PUBLIC_META = """
    query productsMeta($id: ID!){
        product(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_product_as_anonymous_user(api_client, product):
    # given
    product.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    product.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    # when
    response = api_client.post_graphql(QUERY_PRODUCT_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["product"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_product_as_customer(user_api_client, product):
    # given
    product.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    product.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

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
    product.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    product.save(update_fields=["meta"])
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


def test_query_public_meta_for_product_as_service_account(
    service_account_api_client, product, permission_manage_products
):
    # given
    product.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    product.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    # when
    response = service_account_api_client.post_graphql(
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
    product_type.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    product_type.save(update_fields=["meta"])
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
    product_type.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    product_type.save(update_fields=["meta"])
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
    product_type.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    product_type.save(update_fields=["meta"])
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


def test_query_public_meta_for_product_type_as_service_account(
    service_account_api_client, product_type, permission_manage_products
):
    # given
    product_type.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    product_type.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.pk)}

    # when
    response = service_account_api_client.post_graphql(
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
    query productVariantMeta($id: ID!){
        productVariant(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_product_variant_as_anonymous_user(api_client, variant):
    # given
    variant.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    variant.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}

    # when
    response = api_client.post_graphql(QUERY_PRODUCT_VARIANT_PUBLIC_META, variables)
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productVariant"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_product_variant_as_customer(user_api_client, variant):
    # given
    variant.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    variant.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}

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
    variant.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    variant.save(update_fields=["meta"])
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


def test_query_public_meta_for_product_variant_as_service_account(
    service_account_api_client, variant, permission_manage_products
):
    # given
    variant.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    variant.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}

    # when
    response = service_account_api_client.post_graphql(
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


QUERY_SERVICE_ACCOUNT_PUBLIC_META = """
    query serviceAccountMeta($id: ID!){
        serviceAccount(id: $id){
            metadata{
                key
                value
            }
        }
    }
"""


def test_query_public_meta_for_service_account_as_anonymous_user(
    api_client, service_account
):
    # given
    variables = {"id": graphene.Node.to_global_id("ServiceAccount", service_account.pk)}

    # when
    response = api_client.post_graphql(QUERY_SERVICE_ACCOUNT_PUBLIC_META, variables)

    # then
    assert_no_permission(response)


def test_query_public_meta_for_service_account_as_customer(
    user_api_client, service_account
):
    # given
    variables = {"id": graphene.Node.to_global_id("ServiceAccount", service_account.pk)}

    # when
    response = user_api_client.post_graphql(
        QUERY_SERVICE_ACCOUNT_PUBLIC_META, variables
    )

    # then
    assert_no_permission(response)


def test_query_public_meta_for_service_account_as_staff(
    staff_api_client, service_account, permission_manage_service_accounts
):
    # given
    service_account.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    service_account.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("ServiceAccount", service_account.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_SERVICE_ACCOUNT_PUBLIC_META,
        variables,
        [permission_manage_service_accounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["serviceAccount"]["metadata"][0]
    assert metadata["key"] == PUBLIC_KEY
    assert metadata["value"] == PUBLIC_VALUE


def test_query_public_meta_for_service_account_as_service_account(
    service_account_api_client, service_account, permission_manage_service_accounts
):
    # given
    service_account.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    service_account.save(update_fields=["meta"])
    variables = {"id": graphene.Node.to_global_id("ServiceAccount", service_account.pk)}

    # when
    response = service_account_api_client.post_graphql(
        QUERY_SERVICE_ACCOUNT_PUBLIC_META,
        variables,
        [permission_manage_service_accounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["serviceAccount"]["metadata"][0]
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
    me.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    me.save(update_fields=["private_meta"])

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
    customer_user.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    customer_user.save(update_fields=["private_meta"])
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


def test_query_private_meta_for_customer_as_service_account(
    service_account_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    customer_user.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = service_account_api_client.post_graphql(
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
    admin_user.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    admin_user.save(update_fields=["private_meta"])
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


def test_query_private_meta_for_staff_as_service_account(
    service_account_api_client, permission_manage_staff, admin_user
):
    # given
    admin_user.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    admin_user.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("User", admin_user.pk)}

    # when
    response = service_account_api_client.post_graphql(
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


# TODO: Restore after #5245
def test_query_private_meta_for_other_customer_checkout_as_anonymous_user(
    api_client, checkout, customer_user
):
    # given
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"token": checkout.pk}

    # when
    response = api_client.post_graphql(QUERY_CHECKOUT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


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
    checkout.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    checkout.save(update_fields=["user", "private_meta"])
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


def test_query_private_meta_for_checkout_as_service_account(
    service_account_api_client, checkout, customer_user, permission_manage_checkouts
):
    # given
    checkout.user = customer_user
    checkout.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    checkout.save(update_fields=["user", "private_meta"])
    variables = {"token": checkout.pk}

    # when
    response = service_account_api_client.post_graphql(
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
    variables = {"token": order.token}

    # when
    response = api_client.post_graphql(QUERY_ORDER_BY_TOKEN_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_order_by_token_as_customer(user_api_client, order):
    # given
    order.user = user_api_client.user
    order.save(update_fields=["user"])
    variables = {"token": order.token}

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
    order.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["user", "private_meta"])
    variables = {"token": order.token}

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


def test_query_private_meta_for_order_by_token_as_service_account(
    service_account_api_client, order, customer_user, permission_manage_orders
):
    # given
    order.user = customer_user
    order.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["user", "private_meta"])
    variables = {"token": order.token}

    # when
    response = service_account_api_client.post_graphql(
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
    order.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["user", "private_meta"])
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


# TODO: Restore after #5251
# def test_query_private_meta_for_order_as_service_account(
#     service_account_api_client, order, customer_user, permission_manage_orders
# ):
#     # given
#     order.user = customer_user
#     order.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
#     order.save(update_fields=["user", "private_meta"])
#     variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

#     # when
#     response = service_account_api_client.post_graphql(
#         QUERY_ORDER_PRIVATE_META,
#         variables,
#         [permission_manage_orders],
#         check_no_permissions=False,
#     )
#     content = get_graphql_content(response)

#     # then
#     metadata = content["data"]["order"]["privateMetadata"][0]
#     assert metadata["key"] == PRIVATE_KEY
#     assert metadata["value"] == PRIVATE_VALUE


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
    draft_order.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    draft_order.save(update_fields=["user", "private_meta"])
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
    draft_order.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    draft_order.save(update_fields=["user", "private_meta"])
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


# TODO: Restore after #5251
# def test_query_private_meta_for_draft_order_as_service_account(
#     service_account_api_client, draft_order, customer_user, permission_manage_orders
# ):
#     # given
#     draft_order.user = customer_user
#     draft_order.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
#     draft_order.save(update_fields=["user", "private_meta"])
#     variables = {"id": graphene.Node.to_global_id("Order", draft_order.pk)}

#     # when
#     response = service_account_api_client.post_graphql(
#         QUERY_ORDER_PRIVATE_META,
#         variables,
#         [permission_manage_orders],
#         check_no_permissions=False,
#     )
#     content = get_graphql_content(response)

#     # then
#     metadata = content["data"]["order"]["privateMetadata"][0]
#     assert metadata["key"] == PRIVATE_KEY
#     assert metadata["value"] == PRIVATE_VALUE


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
    variables = {"token": fulfilled_order.token}

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
    variables = {"token": fulfilled_order.token}

    # when
    response = user_api_client.post_graphql(QUERY_FULFILLMENT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_fulfillment_as_staff(
    staff_api_client, fulfilled_order, customer_user, permission_manage_orders
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    fulfillment.save(update_fields=["private_meta"])
    fulfilled_order.user = customer_user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.token}

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


def test_query_private_meta_for_fulfillment_as_service_account(
    service_account_api_client, fulfilled_order, customer_user, permission_manage_orders
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    fulfillment.save(update_fields=["private_meta"])
    fulfilled_order.user = customer_user
    fulfilled_order.save(update_fields=["user"])
    variables = {"token": fulfilled_order.token}

    # when
    response = service_account_api_client.post_graphql(
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
    staff_api_client, color_attribute, permission_manage_products
):
    # given
    color_attribute.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    color_attribute.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ATTRIBUTE_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["attribute"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_attribute_as_service_account(
    service_account_api_client, color_attribute, permission_manage_products
):
    # given
    color_attribute.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    color_attribute.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("Attribute", color_attribute.pk)}

    # when
    response = service_account_api_client.post_graphql(
        QUERY_ATTRIBUTE_PRIVATE_META,
        variables,
        [permission_manage_products],
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
    category.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    category.save(update_fields=["private_meta"])
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


def test_query_private_meta_for_category_as_service_account(
    service_account_api_client, category, permission_manage_products
):
    # given
    category.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    category.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = service_account_api_client.post_graphql(
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
    query collectionMeta($id: ID!){
        collection(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_collection_as_anonymous_user(api_client, collection):
    # given
    variables = {"id": graphene.Node.to_global_id("Collection", collection.pk)}

    # when
    response = api_client.post_graphql(QUERY_COLLECTION_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_collection_as_customer(user_api_client, collection):
    # given
    variables = {"id": graphene.Node.to_global_id("Collection", collection.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_COLLECTION_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_collection_as_staff(
    staff_api_client, collection, permission_manage_products
):
    # given
    collection.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    collection.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("Collection", collection.pk)}

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


def test_query_private_meta_for_collection_as_service_account(
    service_account_api_client, collection, permission_manage_products
):
    # given
    collection.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    collection.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("Collection", collection.pk)}

    # when
    response = service_account_api_client.post_graphql(
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
    digital_content.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    digital_content.save(update_fields=["private_meta"])
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
    digital_content.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    digital_content.save(update_fields=["private_meta"])
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


def test_query_private_meta_for_digital_content_as_service_account(
    service_account_api_client, digital_content, permission_manage_products
):
    # given
    digital_content.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    digital_content.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("DigitalContent", digital_content.pk)}

    # when
    response = service_account_api_client.post_graphql(
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


QUERY_PRODUCT_PRIVATE_META = """
    query productsMeta($id: ID!){
        product(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_product_as_anonymous_user(api_client, product):
    # given
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    # when
    response = api_client.post_graphql(QUERY_PRODUCT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_product_as_customer(user_api_client, product):
    # given
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_PRODUCT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_product_as_staff(
    staff_api_client, product, permission_manage_products
):
    # given
    product.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    product.save(update_fields=["private_meta"])
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


def test_query_private_meta_for_product_as_service_account(
    service_account_api_client, product, permission_manage_products
):
    # given
    product.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    product.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    # when
    response = service_account_api_client.post_graphql(
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
    staff_api_client, product_type, permission_manage_products
):
    # given
    product_type.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    product_type.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_TYPE_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productType"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_product_type_as_service_account(
    service_account_api_client, product_type, permission_manage_products
):
    # given
    product_type.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    product_type.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.pk)}

    # when
    response = service_account_api_client.post_graphql(
        QUERY_PRODUCT_TYPE_PRIVATE_META,
        variables,
        [permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["productType"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


QUERY_PRODUCT_VARIANT_PRIVATE_META = """
    query productVariantMeta($id: ID!){
        productVariant(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_product_variant_as_anonymous_user(api_client, variant):
    # given
    variant.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    variant.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}

    # when
    response = api_client.post_graphql(QUERY_PRODUCT_VARIANT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_product_variant_as_customer(user_api_client, variant):
    # given
    variant.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    variant.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}

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
    variant.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    variant.save(update_fields=["private_meta"])
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


def test_query_private_meta_for_product_variant_as_service_account(
    service_account_api_client, variant, permission_manage_products
):
    # given
    variant.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    variant.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}

    # when
    response = service_account_api_client.post_graphql(
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


QUERY_SERVICE_ACCOUNT_PRIVATE_META = """
    query serviceAccountMeta($id: ID!){
        serviceAccount(id: $id){
            privateMetadata{
                key
                value
            }
        }
    }
"""


def test_query_private_meta_for_service_account_as_anonymous_user(
    api_client, service_account
):
    # given
    variables = {"id": graphene.Node.to_global_id("ServiceAccount", service_account.pk)}

    # when
    response = api_client.post_graphql(QUERY_SERVICE_ACCOUNT_PRIVATE_META, variables)

    # then
    assert_no_permission(response)


def test_query_private_meta_for_service_account_as_customer(
    user_api_client, service_account
):
    # given
    variables = {"id": graphene.Node.to_global_id("ServiceAccount", service_account.pk)}

    # when
    response = user_api_client.post_graphql(
        QUERY_SERVICE_ACCOUNT_PRIVATE_META, variables
    )

    # then
    assert_no_permission(response)


def test_query_private_meta_for_service_account_as_staff(
    staff_api_client, service_account, permission_manage_service_accounts
):
    # given
    service_account.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    service_account.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("ServiceAccount", service_account.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_SERVICE_ACCOUNT_PRIVATE_META,
        variables,
        [permission_manage_service_accounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["serviceAccount"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


def test_query_private_meta_for_service_account_as_service_account(
    service_account_api_client, service_account, permission_manage_service_accounts
):
    # given
    service_account.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    service_account.save(update_fields=["private_meta"])
    variables = {"id": graphene.Node.to_global_id("ServiceAccount", service_account.pk)}

    # when
    response = service_account_api_client.post_graphql(
        QUERY_SERVICE_ACCOUNT_PRIVATE_META,
        variables,
        [permission_manage_service_accounts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    metadata = content["data"]["serviceAccount"]["privateMetadata"][0]
    assert metadata["key"] == PRIVATE_KEY
    assert metadata["value"] == PRIVATE_VALUE


UPDATE_PUBLIC_METADATA_MUTATION = """
mutation UpdatePublicMetadata($id: ID!, $input: MetadataItemInput!) {
    updateMetadata(
        id: $id
        input: $input
    ) {
        metadataErrors{
            field
            code
        }
        item {
            metadata{
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


def execute_update_public_metadata_for_item(
    client, permissions, item_id, item_type, key=PUBLIC_KEY, value=PUBLIC_VALUE,
):
    variables = {
        "id": item_id,
        "input": {"key": key, "value": value},
    }

    response = client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


def item_contains_proper_public_metadata(
    item_from_response, item, item_id, key=PUBLIC_KEY, value=PUBLIC_VALUE,
):
    if item_from_response["id"] != item_id:
        return False
    item.refresh_from_db()
    return item.get_meta(key) == value


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
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], customer_user, customer_id
    )


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
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], customer_user, customer_id
    )


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
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], admin_user, admin_id
    )


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
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], admin_user, admin_id
    )


def test_add_public_metadata_for_myself_as_customer(user_api_client):
    # given
    customer = user_api_client.user
    customer_id = graphene.Node.to_global_id("User", customer.pk)

    # when
    response = execute_update_public_metadata_for_item(
        user_api_client, None, customer_id, "User"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], customer, customer_id
    )


def test_add_public_metadata_for_myself_as_staff(staff_api_client):
    # given
    staff = staff_api_client.user
    staff_id = graphene.Node.to_global_id("User", staff.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, None, staff_id, "User"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], staff, staff_id
    )


def test_add_public_metadata_for_checkout(api_client, checkout):
    # given
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], checkout, checkout_id
    )


def test_add_public_metadata_for_order(api_client, order):
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


def test_add_public_metadata_for_draft_order(api_client, draft_order):
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
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], color_attribute, attribute_id
    )


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
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], category, category_id
    )


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
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], collection, collection_id
    )


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
        response["data"]["updateMetadata"]["item"], digital_content, digital_content_id
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
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], product, product_id
    )


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
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], product_type, product_type_id
    )


def test_add_public_metadata_for_product_variant(
    staff_api_client, permission_manage_products, variant
):
    # given
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_products, variant_id, "ProductVariant",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], variant, variant_id
    )


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
        response["data"]["updateMetadata"]["item"], service_account, service_account_id
    )


def test_update_public_metadata_for_item(api_client, checkout):
    # given
    checkout.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.save(update_fields=["meta"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout", value="NewMetaValue"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        checkout,
        checkout_id,
        value="NewMetaValue",
    )


def test_update_public_metadata_for_non_exist_item(api_client):
    # given
    checkout_id = base64.b64encode(b"Checkout:INVALID").decode("utf-8")

    # when
    response = execute_update_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout"
    )

    # then
    errors = response["data"]["updateMetadata"]["metadataErrors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetadataErrorCode.NOT_FOUND.name


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
    errors = response["data"]["updateMetadata"]["metadataErrors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetadataErrorCode.INVALID.name


DELETE_PUBLIC_METADATA_MUTATION = """
mutation DeletePublicMetadata($id: ID!, $key: String!) {
    deleteMetadata(
        id: $id
        key: $key
    ) {
        metadataErrors{
            field
            code
        }
        item {
            metadata{
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


def execute_clear_public_metadata_for_item(
    client, permissions, item_id, item_type, key=PUBLIC_KEY,
):
    variables = {
        "id": item_id,
        "key": key,
    }

    response = client.post_graphql(
        DELETE_PUBLIC_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


def item_without_public_metadata(
    item_from_response, item, item_id, key=PUBLIC_KEY, value=PUBLIC_VALUE,
):
    if item_from_response["id"] != item_id:
        return False
    item.refresh_from_db()
    return item.get_meta(key) != value


def test_delete_public_metadata_for_customer_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    customer_user.save(update_fields=["meta"])
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], customer_user, customer_id
    )


def test_delete_public_metadata_for_customer_as_service_account(
    service_account_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    customer_user.save(update_fields=["meta"])
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        service_account_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], customer_user, customer_id
    )


def test_delete_public_metadata_for_other_staff_as_staff(
    staff_api_client, permission_manage_staff, admin_user
):
    # given
    assert admin_user.pk != staff_api_client.user.pk
    admin_user.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    admin_user.save(update_fields=["meta"])
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_staff, admin_id, "User"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], admin_user, admin_id
    )


def test_delete_public_metadata_for_staff_as_service_account(
    service_account_api_client, permission_manage_staff, admin_user
):
    # given
    admin_user.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    admin_user.save(update_fields=["meta"])
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        service_account_api_client, permission_manage_staff, admin_id, "User"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], admin_user, admin_id
    )


def test_delete_public_metadata_for_myself_as_customer(user_api_client):
    # given
    customer = user_api_client.user
    customer.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    customer.save(update_fields=["meta"])
    customer_id = graphene.Node.to_global_id("User", customer.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        user_api_client, None, customer_id, "User"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], customer, customer_id
    )


def test_delete_public_metadata_for_myself_as_staff(staff_api_client):
    # given
    staff = staff_api_client.user
    staff.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    staff.save(update_fields=["meta"])
    staff_id = graphene.Node.to_global_id("User", staff.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, None, staff_id, "User"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], staff, staff_id
    )


def test_delete_public_metadata_for_checkout(api_client, checkout):
    # given
    checkout.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.save(update_fields=["meta"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], checkout, checkout_id
    )


def test_delete_public_metadata_for_order(api_client, order):
    # given
    order.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    order.save(update_fields=["meta"])
    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, order_id, "Order"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], order, order_id
    )


def test_delete_public_metadata_for_draft_order(api_client, draft_order):
    # given
    draft_order.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    draft_order.save(update_fields=["meta"])
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, draft_order_id, "Order"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], draft_order, draft_order_id
    )


def test_delete_public_metadata_for_attribute(
    staff_api_client, permission_manage_products, color_attribute
):
    # given
    color_attribute.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    color_attribute.save(update_fields=["meta"])
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, attribute_id, "Attribute"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], color_attribute, attribute_id
    )


def test_delete_public_metadata_for_category(
    staff_api_client, permission_manage_products, category
):
    # given
    category.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    category.save(update_fields=["meta"])
    category_id = graphene.Node.to_global_id("Category", category.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, category_id, "Category"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], category, category_id
    )


def test_delete_public_metadata_for_collection(
    staff_api_client, permission_manage_products, collection
):
    # given
    collection.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    collection.save(update_fields=["meta"])
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, collection_id, "Collection"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], collection, collection_id
    )


def test_delete_public_metadata_for_digital_content(
    staff_api_client, permission_manage_products, digital_content
):
    # given
    digital_content.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    digital_content.save(update_fields=["meta"])
    digital_content_id = graphene.Node.to_global_id(
        "DigitalContent", digital_content.pk
    )

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        digital_content_id,
        "DigitalContent",
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], digital_content, digital_content_id
    )


def test_delete_public_metadata_for_fulfillment(
    staff_api_client, permission_manage_orders, fulfillment
):
    # given
    fulfillment.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    fulfillment.save(update_fields=["meta"])
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_orders, fulfillment_id, "Fulfillment"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], fulfillment, fulfillment_id
    )


def test_delete_public_metadata_for_product(
    staff_api_client, permission_manage_products, product
):
    # given
    product.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    product.save(update_fields=["meta"])
    product_id = graphene.Node.to_global_id("Product", product.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, product_id, "Product"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], product, product_id
    )


def test_delete_public_metadata_for_product_type(
    staff_api_client, permission_manage_products, product_type
):
    # given
    product_type.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    product_type.save(update_fields=["meta"])
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, product_type_id, "ProductType"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], product_type, product_type_id
    )


def test_delete_public_metadata_for_product_variant(
    staff_api_client, permission_manage_products, variant
):
    # given
    variant.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    variant.save(update_fields=["meta"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, variant_id, "ProductVariant"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], variant, variant_id
    )


def test_delete_public_metadata_for_service_account(
    staff_api_client, permission_manage_service_accounts, service_account
):
    # given
    service_account_id = graphene.Node.to_global_id(
        "ServiceAccount", service_account.pk
    )

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client,
        permission_manage_service_accounts,
        service_account_id,
        "ServiceAccount",
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], service_account, service_account_id
    )


def test_delete_public_metadata_for_non_exist_item(api_client):
    # given
    checkout_id = base64.b64encode(b"Checkout:INVALID").decode("utf-8")

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout"
    )

    # then
    errors = response["data"]["deleteMetadata"]["metadataErrors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetadataErrorCode.NOT_FOUND.name


def test_delete_public_metadata_for_item_without_meta(api_client, address):
    # given
    assert not issubclass(type(address), ModelWithMetadata)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    # We use "User" type inside mutation for valid graphql query with fragment
    # without this we are not able to reuse DELETE_PUBLIC_METADATA_MUTATION
    response = execute_clear_public_metadata_for_item(
        api_client, None, address_id, "User"
    )

    # then
    errors = response["data"]["deleteMetadata"]["metadataErrors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetadataErrorCode.INVALID.name


def test_delete_public_metadata_for_not_exist_key(api_client, checkout):
    # given
    checkout.store_meta({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.save(update_fields=["meta"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout", key="Not-exits"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["deleteMetadata"]["item"], checkout, checkout_id
    )


def test_delete_public_metadata_for_one_key(api_client, checkout):
    # given
    checkout.store_meta({PUBLIC_KEY: PUBLIC_VALUE, "to_clear": PUBLIC_VALUE},)
    checkout.save(update_fields=["meta"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout", key="to_clear"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["deleteMetadata"]["item"], checkout, checkout_id
    )
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"],
        checkout,
        checkout_id,
        key="to_clear",
    )


UPDATE_PRIVATE_METADATA_MUTATION = """
mutation UpdatePrivateMetadata($id: ID!, $input: MetadataItemInput!) {
    updatePrivateMetadata(
        id: $id
        input: $input
    ) {
        metadataErrors{
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
    client, permissions, item_id, item_type, key=PRIVATE_KEY, value=PRIVATE_VALUE,
):
    variables = {
        "id": item_id,
        "input": {"key": key, "value": value},
    }

    response = client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


def item_contains_proper_private_metadata(
    item_from_response, item, item_id, key=PRIVATE_KEY, value=PRIVATE_VALUE,
):
    if item_from_response["id"] != item_id:
        return False
    item.refresh_from_db()
    return item.get_private_meta(key) == value


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


def test_add_private_metadata_for_customer_as_service_account(
    service_account_api_client, permission_manage_users, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_update_private_metadata_for_item(
        service_account_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_contains_proper_private_metadata(
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


def test_add_private_metadata_for_staff_as_service_account(
    service_account_api_client, permission_manage_staff, admin_user
):
    # given
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_update_private_metadata_for_item(
        service_account_api_client, permission_manage_staff, admin_id, "User"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], admin_user, admin_id
    )


def test_add_private_metadata_for_myself_as_customer_no_permission(user_api_client):
    # given
    customer = user_api_client.user
    variables = {
        "id": graphene.Node.to_global_id("User", customer.pk),
        "input": {"key": PRIVATE_KEY, "value": PRIVATE_VALUE},
    }

    # when
    response = user_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "User", variables, permissions=[],
    )

    # then
    assert_no_permission(response)


def test_add_private_metadata_for_myself_as_staff(staff_api_client):
    # given
    staff = staff_api_client.user
    variables = {
        "id": graphene.Node.to_global_id("User", staff.pk),
        "input": {"key": PRIVATE_KEY, "value": PRIVATE_VALUE},
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "User", variables, permissions=[],
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
        response["data"]["updatePrivateMetadata"]["item"], checkout, checkout_id
    )


def test_add_private_metadata_for_order(
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


def test_add_private_metadata_for_draft_order(
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


def test_add_private_metadata_for_attribute(
    staff_api_client, permission_manage_products, color_attribute
):
    # given
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_products, attribute_id, "Attribute"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], color_attribute, attribute_id
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
    staff_api_client, permission_manage_products, collection
):
    # given
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


def test_add_private_metadata_for_product(
    staff_api_client, permission_manage_products, product
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


def test_add_private_metadata_for_product_type(
    staff_api_client, permission_manage_products, product_type
):
    # given
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_products, product_type_id, "ProductType"
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
        staff_api_client, permission_manage_products, variant_id, "ProductVariant",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], variant, variant_id
    )


def test_add_private_metadata_for_service_account(
    staff_api_client, permission_manage_service_accounts, service_account
):
    # given
    service_account_id = graphene.Node.to_global_id(
        "ServiceAccount", service_account.pk
    )

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_service_accounts,
        service_account_id,
        "ServiceAccount",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        service_account,
        service_account_id,
    )


def test_update_private_metadata_for_item(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout.store_private_meta({PRIVATE_KEY: PRIVATE_KEY})
    checkout.save(update_fields=["private_meta"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_checkouts,
        checkout_id,
        "Checkout",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        checkout,
        checkout_id,
        value="NewMetaValue",
    )


def test_update_private_metadata_for_non_exist_item(
    staff_api_client, permission_manage_checkouts
):
    # given
    checkout_id = base64.b64encode(b"Checkout:INVALID").decode("utf-8")

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout_id, "Checkout"
    )

    # then
    errors = response["data"]["updatePrivateMetadata"]["metadataErrors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetadataErrorCode.NOT_FOUND.name


def test_update_private_metadata_for_item_without_meta(api_client, address):
    # given
    assert not issubclass(type(address), ModelWithMetadata)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    # We use "User" type inside mutation for valid graphql query with fragment
    # without this we are not able to reuse UPDATE_PRIVATE_METADATA_MUTATION
    response = execute_update_private_metadata_for_item(
        api_client, None, address_id, "User"
    )

    # then
    errors = response["data"]["updatePrivateMetadata"]["metadataErrors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetadataErrorCode.INVALID.name


DELETE_PRIVATE_METADATA_MUTATION = """
mutation DeletePrivateMetadata($id: ID!, $key: String!) {
    deletePrivateMetadata(
        id: $id
        key: $key
    ) {
        metadataErrors{
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
    client, permissions, item_id, item_type, key=PRIVATE_KEY,
):
    variables = {
        "id": item_id,
        "key": key,
    }

    response = client.post_graphql(
        DELETE_PRIVATE_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


def item_without_private_metadata(
    item_from_response, item, item_id, key=PRIVATE_KEY, value=PRIVATE_VALUE,
):
    if item_from_response["id"] != item_id:
        return False
    item.refresh_from_db()
    return item.get_private_meta(key) != value


def test_delete_private_metadata_for_customer_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    customer_user.save(update_fields=["private_meta"])
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], customer_user, customer_id
    )


def test_delete_private_metadata_for_customer_as_service_account(
    service_account_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    customer_user.save(update_fields=["private_meta"])
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        service_account_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], customer_user, customer_id
    )


def test_delete_private_metadata_for_other_staff_as_staff(
    staff_api_client, permission_manage_staff, admin_user
):
    # given
    assert admin_user.pk != staff_api_client.user.pk
    admin_user.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    admin_user.save(update_fields=["private_meta"])
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_staff, admin_id, "User"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], admin_user, admin_id
    )


def test_delete_private_metadata_for_staff_as_service_account(
    service_account_api_client, permission_manage_staff, admin_user
):
    # given
    admin_user.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    admin_user.save(update_fields=["private_meta"])
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        service_account_api_client, permission_manage_staff, admin_id, "User"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], admin_user, admin_id
    )


def test_delete_private_metadata_for_myself_as_customer_no_permission(user_api_client):
    # given
    customer = user_api_client.user
    customer.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    customer.save(update_fields=["private_meta"])
    variables = {
        "id": graphene.Node.to_global_id("User", customer.pk),
        "key": PRIVATE_KEY,
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
    staff.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    staff.save(update_fields=["private_meta"])
    variables = {
        "id": graphene.Node.to_global_id("User", staff.pk),
        "key": PRIVATE_KEY,
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
    checkout.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    checkout.save(update_fields=["private_meta"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout_id, "Checkout"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], checkout, checkout_id
    )


def test_delete_private_metadata_for_order(
    staff_api_client, order, permission_manage_orders
):
    # given
    order.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    order.save(update_fields=["private_meta"])
    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, order_id, "Order"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], order, order_id
    )


def test_delete_private_metadata_for_draft_order(
    staff_api_client, draft_order, permission_manage_orders
):
    # given
    draft_order.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    draft_order.save(update_fields=["private_meta"])
    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, draft_order_id, "Order"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], draft_order, draft_order_id
    )


def test_delete_private_metadata_for_attribute(
    staff_api_client, permission_manage_products, color_attribute
):
    # given
    color_attribute.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    color_attribute.save(update_fields=["private_meta"])
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, attribute_id, "Attribute"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], color_attribute, attribute_id
    )


def test_delete_private_metadata_for_category(
    staff_api_client, permission_manage_products, category
):
    # given
    category.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    category.save(update_fields=["private_meta"])
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
    staff_api_client, permission_manage_products, collection
):
    # given
    collection.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    collection.save(update_fields=["private_meta"])
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
    digital_content.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    digital_content.save(update_fields=["private_meta"])
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
    fulfillment.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    fulfillment.save(update_fields=["private_meta"])
    fulfillment_id = graphene.Node.to_global_id("Fulfillment", fulfillment.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_orders, fulfillment_id, "Fulfillment"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], fulfillment, fulfillment_id
    )


def test_delete_private_metadata_for_product(
    staff_api_client, permission_manage_products, product
):
    # given
    product.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    product.save(update_fields=["private_meta"])
    product_id = graphene.Node.to_global_id("Product", product.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, product_id, "Product"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], product, product_id
    )


def test_delete_private_metadata_for_product_type(
    staff_api_client, permission_manage_products, product_type
):
    # given
    product_type.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    product_type.save(update_fields=["private_meta"])
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, product_type_id, "ProductType"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], product_type, product_type_id
    )


def test_delete_private_metadata_for_product_variant(
    staff_api_client, permission_manage_products, variant
):
    # given
    variant.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    variant.save(update_fields=["private_meta"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, variant_id, "ProductVariant"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], variant, variant_id
    )


def test_delete_private_metadata_for_service_account(
    staff_api_client, permission_manage_service_accounts, service_account
):
    # given
    service_account_id = graphene.Node.to_global_id(
        "ServiceAccount", service_account.pk
    )

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_service_accounts,
        service_account_id,
        "ServiceAccount",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        service_account,
        service_account_id,
    )


def test_delete_private_metadata_for_non_exist_item(
    staff_api_client, permission_manage_checkouts
):
    # given
    checkout_id = base64.b64encode(b"Checkout:INVALID").decode("utf-8")

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_checkouts, checkout_id, "Checkout"
    )

    # then
    errors = response["data"]["deletePrivateMetadata"]["metadataErrors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetadataErrorCode.NOT_FOUND.name


def test_delete_private_metadata_for_item_without_meta(api_client, address):
    # given
    assert not issubclass(type(address), ModelWithMetadata)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    # We use "User" type inside mutation for valid graphql query with fragment
    # without this we are not able to reuse DELETE_PRIVATE_METADATA_MUTATION
    response = execute_clear_private_metadata_for_item(
        api_client, None, address_id, "User"
    )

    # then
    errors = response["data"]["deletePrivateMetadata"]["metadataErrors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetadataErrorCode.INVALID.name


def test_delete_private_metadata_for_not_exist_key(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout.store_private_meta({PRIVATE_KEY: PRIVATE_VALUE})
    checkout.save(update_fields=["private_meta"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_checkouts,
        checkout_id,
        "Checkout",
        key="Not-exits",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], checkout, checkout_id
    )


def test_delete_private_metadata_for_one_key(
    staff_api_client, checkout, permission_manage_checkouts
):
    # given
    checkout.store_private_meta(
        {PRIVATE_KEY: PRIVATE_VALUE, "to_clear": PRIVATE_VALUE},
    )
    checkout.save(update_fields=["private_meta"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_checkouts,
        checkout_id,
        "Checkout",
        key="to_clear",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], checkout, checkout_id
    )
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        checkout,
        checkout_id,
        key="to_clear",
    )
