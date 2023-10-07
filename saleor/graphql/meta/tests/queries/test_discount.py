import graphene

from ....tests.utils import assert_no_permission, get_graphql_content
from .utils import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE

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
