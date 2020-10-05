import graphene

from ...tests.utils import assert_graphql_error_with_message, get_graphql_content

VARIANT_QUERY = """
query variant($id: ID, $sku: String){
    productVariant(id:$id, sku:$sku){
        sku
    }
}
"""


def test_get_variant_without_id_and_sku(staff_api_client, permission_manage_products):
    # given

    # when
    response = staff_api_client.post_graphql(
        VARIANT_QUERY,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    assert_graphql_error_with_message(
        response, "Either 'id'  or 'sku' argument is required"
    )


def test_get_variant_with_id_and_sku(staff_api_client, permission_manage_products):
    # given
    variables = {"id": "ID", "sku": "sku"}

    # when
    response = staff_api_client.post_graphql(
        VARIANT_QUERY,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    assert_graphql_error_with_message(
        response, "Argument 'id' cannot be combined with 'sku'"
    )


def test_get_unpublished_variant_by_id_as_staff(
    staff_api_client, permission_manage_products, unavailable_product_with_variant
):
    # given
    variant = unavailable_product_with_variant.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}

    # when
    response = staff_api_client.post_graphql(
        VARIANT_QUERY,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


def test_get_unpublished_variant_by_id_as_app(
    app_api_client, permission_manage_products, unavailable_product_with_variant
):
    # given
    variant = unavailable_product_with_variant.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}

    # when
    response = app_api_client.post_graphql(
        VARIANT_QUERY,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


def test_get_unpublished_variant_by_id_as_customer(
    user_api_client, unavailable_product_with_variant
):
    # given
    variant = unavailable_product_with_variant.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}

    # when
    response = user_api_client.post_graphql(
        VARIANT_QUERY, variables, check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]


def test_get_unpublished_variant_by_id_as_anonymous_user(
    api_client, unavailable_product_with_variant
):
    # given
    variant = unavailable_product_with_variant.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}

    # when
    response = api_client.post_graphql(
        VARIANT_QUERY, variables, check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]


def test_get_variant_by_id_as_staff(
    staff_api_client, permission_manage_products, variant
):
    # given
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}

    # when
    response = staff_api_client.post_graphql(
        VARIANT_QUERY,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


def test_get_variant_by_id_as_app(app_api_client, permission_manage_products, variant):
    # given
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}

    # when
    response = app_api_client.post_graphql(
        VARIANT_QUERY,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


def test_get_variant_by_id_as_customer(user_api_client, variant):
    # given
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}

    # when
    response = user_api_client.post_graphql(
        VARIANT_QUERY, variables, check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


def test_get_variant_by_id_as_anonymous_user(api_client, variant):
    # given
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}

    # when
    response = api_client.post_graphql(
        VARIANT_QUERY, variables, check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


def test_get_unpublished_variant_by_sku_as_staff(
    staff_api_client, permission_manage_products, unavailable_product_with_variant
):
    # given
    variant = unavailable_product_with_variant.variants.first()
    variables = {"sku": variant.sku}

    # when
    response = staff_api_client.post_graphql(
        VARIANT_QUERY,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


def test_get_unpublished_variant_by_sku_as_app(
    app_api_client, permission_manage_products, unavailable_product_with_variant
):
    # given
    variant = unavailable_product_with_variant.variants.first()
    variables = {"sku": variant.sku}

    # when
    response = app_api_client.post_graphql(
        VARIANT_QUERY,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


def test_get_unpublished_variant_by_sku_as_customer(
    user_api_client, unavailable_product_with_variant
):
    # given
    variant = unavailable_product_with_variant.variants.first()
    variables = {"sku": variant.sku}

    # when
    response = user_api_client.post_graphql(
        VARIANT_QUERY, variables, check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]


def test_get_unpublished_variant_by_sku_as_anonymous_user(
    api_client, unavailable_product_with_variant
):
    # given
    variant = unavailable_product_with_variant.variants.first()
    variables = {"sku": variant.sku}

    # when
    response = api_client.post_graphql(
        VARIANT_QUERY, variables, check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]


def test_get_variant_by_sku_as_staff(
    staff_api_client, permission_manage_products, variant
):
    # given
    variables = {"sku": variant.sku}

    # when
    response = staff_api_client.post_graphql(
        VARIANT_QUERY,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


def test_get_variant_by_sku_as_app(app_api_client, permission_manage_products, variant):
    # given
    variables = {"sku": variant.sku}

    # when
    response = app_api_client.post_graphql(
        VARIANT_QUERY,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


def test_get_variant_by_sku_as_customer(user_api_client, variant):
    # given
    variables = {"sku": variant.sku}

    # when
    response = user_api_client.post_graphql(
        VARIANT_QUERY, variables, check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


def test_get_variant_by_sku_as_anonymous_user(api_client, variant):
    # given
    variables = {"sku": variant.sku}

    # when
    response = api_client.post_graphql(
        VARIANT_QUERY, variables, check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku
