import graphene

from ....tests.utils import assert_no_permission, get_graphql_content
from .utils import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE

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


QUERY_PRODUCT_MEDIA_METADATA = """
    query productMediaById(
        $mediaId: ID!,
        $productId: ID!,
        $channel: String,
    ) {
        product(id: $productId, channel: $channel) {
            mediaById(id: $mediaId) {
                metadata {
                    key
                    value
                }
                privateMetadata {
                    key
                    value
                }
            }
        }
    }
"""


def test_query_metadata_for_product_media_as_staff(
    staff_api_client, product_with_image, channel_USD, permission_manage_products
):
    # given
    query = QUERY_PRODUCT_MEDIA_METADATA
    media = product_with_image.media.first()

    metadata = {"label": "image-name"}
    private_metadata = {"private-label": "private-name"}
    media.store_value_in_metadata(metadata)
    media.store_value_in_private_metadata(private_metadata)
    media.save(update_fields=["metadata", "private_metadata"])

    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": graphene.Node.to_global_id("ProductMedia", media.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["product"]["mediaById"]
    assert data["metadata"][0]["key"] in metadata.keys()
    assert data["metadata"][0]["value"] in metadata.values()
    assert data["privateMetadata"][0]["key"] in private_metadata.keys()
    assert data["privateMetadata"][0]["value"] in private_metadata.values()


def test_query_metadata_for_product_media_as_app(
    app_api_client, product_with_image, channel_USD, permission_manage_products
):
    # given
    query = QUERY_PRODUCT_MEDIA_METADATA
    media = product_with_image.media.first()

    metadata = {"label": "image-name"}
    private_metadata = {"private-label": "private-name"}
    media.store_value_in_metadata(metadata)
    media.store_value_in_private_metadata(private_metadata)
    media.save(update_fields=["metadata", "private_metadata"])

    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": graphene.Node.to_global_id("ProductMedia", media.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["product"]["mediaById"]
    assert data["metadata"][0]["key"] in metadata.keys()
    assert data["metadata"][0]["value"] in metadata.values()
    assert data["privateMetadata"][0]["key"] in private_metadata.keys()
    assert data["privateMetadata"][0]["value"] in private_metadata.values()


def test_query_metadata_for_product_media_as_anonymous_user(
    api_client, product_with_image, channel_USD
):
    # given
    query = QUERY_PRODUCT_MEDIA_METADATA
    media = product_with_image.media.first()
    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": graphene.Node.to_global_id("ProductMedia", media.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_query_metadata_for_product_media_as_customer_user(
    user_api_client, product_with_image, channel_USD
):
    # given
    query = QUERY_PRODUCT_MEDIA_METADATA
    media = product_with_image.media.first()
    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": graphene.Node.to_global_id("ProductMedia", media.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_query_metadata_for_product_media_as_staff_missing_permissions(
    staff_api_client, product_with_image, channel_USD
):
    # given
    query = QUERY_PRODUCT_MEDIA_METADATA
    media = product_with_image.media.first()

    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": graphene.Node.to_global_id("ProductMedia", media.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)
