import graphene
import pytest

from ....attribute.utils import _associate_attribute_to_instance
from ...tests.utils import assert_graphql_error_with_message, get_graphql_content
from ..enums import VariantAttributeScope

VARIANT_QUERY = """
query variant(
    $id: ID, $sku: String, $variantSelection: VariantAttributeScope, $channel: String
){
    productVariant(id:$id, sku:$sku, channel: $channel){
        sku
        attributes(variantSelection: $variantSelection) {
            attribute {
                slug
            }
        }
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
        response, "At least one of arguments is required: 'id', 'sku'."
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
    user_api_client, unavailable_product_with_variant, channel_USD
):
    # given
    variant = unavailable_product_with_variant.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(
        VARIANT_QUERY, variables, check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]


def test_get_unpublished_variant_by_id_as_anonymous_user(
    api_client, unavailable_product_with_variant, channel_USD
):
    # given
    variant = unavailable_product_with_variant.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

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


def test_get_variant_by_id_as_customer(user_api_client, variant, channel_USD):
    # given
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(
        VARIANT_QUERY, variables, check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


def test_get_variant_by_id_as_anonymous_user(api_client, variant, channel_USD):
    # given
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

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
    user_api_client, unavailable_product_with_variant, channel_USD
):
    # given
    variant = unavailable_product_with_variant.variants.first()
    variables = {"sku": variant.sku, "channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(
        VARIANT_QUERY, variables, check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]


def test_get_unpublished_variant_by_sku_as_anonymous_user(
    api_client, unavailable_product_with_variant, channel_USD
):
    # given
    variant = unavailable_product_with_variant.variants.first()
    variables = {"sku": variant.sku, "channel": channel_USD.slug}

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


def test_get_variant_by_sku_as_customer(user_api_client, variant, channel_USD):
    # given
    variables = {"sku": variant.sku, "channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(
        VARIANT_QUERY, variables, check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


def test_get_variant_by_sku_as_anonymous_user(api_client, variant, channel_USD):
    # given
    variables = {"sku": variant.sku, "channel": channel_USD.slug}

    # when
    response = api_client.post_graphql(
        VARIANT_QUERY, variables, check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


@pytest.mark.parametrize(
    "variant_selection",
    [
        VariantAttributeScope.ALL.name,
        VariantAttributeScope.VARIANT_SELECTION.name,
        VariantAttributeScope.NOT_VARIANT_SELECTION.name,
    ],
)
def test_get_variant_by_id_with_variant_selection_filter(
    variant_selection,
    staff_api_client,
    permission_manage_products,
    variant,
    size_attribute,
    file_attribute_with_file_input_type_without_values,
    product_type,
):
    # given
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "variantSelection": variant_selection}

    product_type.variant_attributes.add(
        file_attribute_with_file_input_type_without_values
    )

    _associate_attribute_to_instance(
        variant, file_attribute_with_file_input_type_without_values.pk
    )
    _associate_attribute_to_instance(variant, size_attribute.pk)

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
    if variant_selection == VariantAttributeScope.NOT_VARIANT_SELECTION.name:
        assert len(data["attributes"]) == 1
        assert (
            data["attributes"][0]["attribute"]["slug"]
            == file_attribute_with_file_input_type_without_values.slug
        )
    elif variant_selection == VariantAttributeScope.VARIANT_SELECTION.name:
        assert len(data["attributes"]) == 1
        assert data["attributes"][0]["attribute"]["slug"] == size_attribute.slug
    else:
        len(data["attributes"]) == 2
