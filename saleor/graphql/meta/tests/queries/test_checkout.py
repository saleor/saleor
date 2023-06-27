from ....tests.utils import assert_no_permission, get_graphql_content
from .utils import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE

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
