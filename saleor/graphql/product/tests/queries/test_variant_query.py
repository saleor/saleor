import graphene
import pytest

from .....attribute.models import AttributeValue
from .....attribute.utils import (
    _associate_attribute_to_instance,
    associate_attribute_values_to_instance,
)
from .....warehouse.models import Stock, Warehouse
from ....tests.utils import (
    assert_graphql_error_with_message,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ...enums import VariantAttributeScope

VARIANT_QUERY = """
query variant(
    $id: ID,
    $sku: String,
    $externalReference: String,
    $variantSelection: VariantAttributeScope,
    $channel: String
){
    productVariant(
        id:$id, sku:$sku, externalReference: $externalReference, channel: $channel
    ){
        id
        sku
        externalReference
        attributes(variantSelection: $variantSelection) {
            attribute {
                slug
            }
            values {
                id
                slug
            }
        }
    }
}
"""


def test_get_variant_without_id_sku_and_external_reference(
    staff_api_client, permission_manage_products
):
    # given

    # when
    response = staff_api_client.post_graphql(
        VARIANT_QUERY,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    assert_graphql_error_with_message(
        response,
        "At least one of arguments is required: 'id', 'sku', 'external_reference'.",
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
        VARIANT_QUERY,
        variables,
        check_no_permissions=False,
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
        VARIANT_QUERY,
        variables,
        check_no_permissions=False,
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
        VARIANT_QUERY,
        variables,
        check_no_permissions=False,
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
        VARIANT_QUERY,
        variables,
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["sku"] == variant.sku


def test_get_variant_without_sku_by_id_as_staff(
    staff_api_client, permission_manage_products, variant
):
    # given
    variant.sku = None
    variant.save()

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
    assert data["id"] == variant_id


def test_get_variant_without_sku_by_id_as_app(
    app_api_client, permission_manage_products, variant
):
    # given
    variant.sku = None
    variant.save()

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
    assert data["id"] == variant_id


def test_get_variant_without_sku_by_id_as_customer(
    user_api_client, variant, channel_USD
):
    # given
    variant.sku = None
    variant.save()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(
        VARIANT_QUERY,
        variables,
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["id"] == variant_id


def test_get_variant_without_sku_by_id_as_anonymous_user(
    api_client, variant, channel_USD
):
    # given
    variant.sku = None
    variant.save()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = api_client.post_graphql(
        VARIANT_QUERY,
        variables,
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["id"] == variant_id


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
        VARIANT_QUERY,
        variables,
        check_no_permissions=False,
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
        VARIANT_QUERY,
        variables,
        check_no_permissions=False,
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


def test_get_variant_by_external_reference(
    staff_api_client, permission_manage_products, variant
):
    # given
    ext_ref = "test-ext-ref"
    variant.external_reference = ext_ref
    variant.save(update_fields=["external_reference"])
    variables = {"externalReference": ext_ref}

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
    assert data["externalReference"] == ext_ref


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
        VARIANT_QUERY,
        variables,
        check_no_permissions=False,
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
        VARIANT_QUERY,
        variables,
        check_no_permissions=False,
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
        variant,
        {
            file_attribute_with_file_input_type_without_values.pk: [],
            size_attribute.pk: [],
        },
    )

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


def test_get_variant_with_sorted_attribute_values(
    staff_api_client,
    variant,
    product_type_product_reference_attribute,
    permission_manage_products,
    product_list,
):
    # given
    product_type = variant.product.product_type
    product_type.variant_attributes.set([product_type_product_reference_attribute])

    attr_value_1 = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_list[0].name,
        slug=f"{variant.pk}_{product_list[0].pk}",
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_list[1].name,
        slug=f"{variant.pk}_{product_list[1].pk}",
    )
    attr_value_3 = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_list[2].name,
        slug=f"{variant.pk}_{product_list[2].pk}",
    )

    attr_values = [attr_value_2, attr_value_1, attr_value_3]
    associate_attribute_values_to_instance(
        variant, {product_type_product_reference_attribute.pk: attr_values}
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"id": variant_id}
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(VARIANT_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert len(data["attributes"]) == 1
    values = data["attributes"][0]["values"]
    assert len(values) == 3
    assert [value["id"] for value in values] == [
        graphene.Node.to_global_id("AttributeValue", val.pk) for val in attr_values
    ]


@pytest.mark.parametrize(
    ("field", "is_nested"),
    [("digitalContent", True), ("quantityOrdered", False)],
)
def test_variant_restricted_fields_permissions(
    staff_api_client,
    permission_manage_products,
    permission_manage_orders,
    product,
    field,
    is_nested,
    channel_USD,
):
    query = f"""
    query ProductVariant($id: ID!, $channel: String) {{
        productVariant(id: $id, channel: $channel) {{
            {field if not is_nested else f"{field} {{ __typename }}"}
        }}
    }}
    """
    variant = product.variants.first()
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
    }
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    assert field in content["data"]["productVariant"]


def test_variant_digital_content(
    staff_api_client, permission_manage_products, digital_content, channel_USD
):
    query = """
    query Margin($id: ID!, $channel: String) {
        productVariant(id: $id, channel: $channel) {
            digitalContent{
                id
            }
        }
    }
    """
    variant = digital_content.product_variant
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
    }
    permissions = [permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    assert "digitalContent" in content["data"]["productVariant"]
    assert "id" in content["data"]["productVariant"]["digitalContent"]


def test_product_variant_without_price_by_sku_as_user(
    user_api_client, variant, channel_USD
):
    query = """
        query getProductVariant($sku: String!, $channel: String) {
            productVariant(sku: $sku, channel: $channel) {
                id
                name
                sku
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)

    variables = {"sku": variant.sku, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data is None


def test_product_variant_without_price_by_sku_as_app_without_permission(
    app_api_client,
    variant,
    channel_USD,
):
    query = """
        query getProductVariant($sku: String!, $channel: String) {
            productVariant(sku: $sku, channel: $channel) {
                id
                name
                sku
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)

    variables = {"sku": variant.sku, "channel": channel_USD.slug}
    response = app_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]


def test_product_variant_without_price_by_sku_as_app_with_permission(
    app_api_client, variant, channel_USD, permission_manage_products
):
    query = """
        query getProductVariant($sku: String!, $channel: String) {
            productVariant(sku: $sku, channel: $channel) {
                id
                name
                sku
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"sku": variant.sku, "channel": channel_USD.slug}
    response = app_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["id"] == variant_id


def test_product_variant_without_price_by_sku_as_staff_without_permission(
    staff_api_client, variant, channel_USD
):
    query = """
        query getProductVariant($sku: String!, $channel: String) {
            productVariant(sku: $sku, channel: $channel) {
                id
                name
                sku
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)

    variables = {"sku": variant.sku, "channel": channel_USD.slug}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]


def test_product_variant_without_price_by_sku_as_staff_with_permission(
    staff_api_client, variant, channel_USD, permission_manage_products
):
    query = """
        query getProductVariant($sku: String!, $channel: String) {
            productVariant(sku: $sku, channel: $channel) {
                id
                name
                sku
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"sku": variant.sku, "channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["id"] == variant_id


QUERY_PRODUCT_VARIANT_BY_ID = """
    query getProductVariant($id: ID!, $channel: String) {
        productVariant(id: $id, channel: $channel) {
            id
            name
            sku
        }
    }
"""


def test_product_variant_without_price_by_id_as_staff_with_permission(
    staff_api_client, variant, channel_USD, permission_manage_products
):
    query = QUERY_PRODUCT_VARIANT_BY_ID
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"id": variant_id, "channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["id"] == variant_id


def test_product_variant_without_price_by_id_as_staff_without_permission(
    staff_api_client, variant, channel_USD
):
    query = QUERY_PRODUCT_VARIANT_BY_ID
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"id": variant_id, "channel": channel_USD.slug}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]


def test_product_variant_without_price_by_id_as_app_without_permission(
    app_api_client, variant, channel_USD
):
    query = QUERY_PRODUCT_VARIANT_BY_ID
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"id": variant_id, "channel": channel_USD.slug}
    response = app_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]


def test_product_variant_without_price_by_id_as_app_with_permission(
    app_api_client, variant, channel_USD, permission_manage_products
):
    query = QUERY_PRODUCT_VARIANT_BY_ID
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"id": variant_id, "channel": channel_USD.slug}
    response = app_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["id"] == variant_id


def test_product_variant_without_price_by_id_as_user(
    user_api_client, variant, channel_USD
):
    query = QUERY_PRODUCT_VARIANT_BY_ID
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"id": variant_id, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data is None


def test_variant_query_invalid_id(user_api_client, variant, channel_USD):
    variant_id = "'"
    variables = {
        "id": variant_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_PRODUCT_VARIANT_BY_ID, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"]
        == f"Invalid ID: {variant_id}. Expected: ProductVariant."
    )
    assert content["data"]["productVariant"] is None


def test_variant_query_object_with_given_id_does_not_exist(
    user_api_client, variant, channel_USD
):
    variant_id = graphene.Node.to_global_id("ProductVariant", -1)
    variables = {
        "id": variant_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_PRODUCT_VARIANT_BY_ID, variables)
    content = get_graphql_content(response)
    assert content["data"]["productVariant"] is None


def test_variant_query_with_invalid_object_type(user_api_client, variant, channel_USD):
    variant_id = graphene.Node.to_global_id("Product", variant.pk)
    variables = {
        "id": variant_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_PRODUCT_VARIANT_BY_ID, variables)
    content = get_graphql_content(response)
    assert content["data"]["productVariant"] is None


def test_stock_quantities_in_different_warehouses(
    api_client, channel_USD, variant_with_many_stocks_different_shipping_zones
):
    query = """
    query ProductVariant(
        $id: ID!, $channel: String!, $country1: CountryCode, $country2: CountryCode
    ) {
        productVariant(id: $id, channel: $channel) {
            quantityPL: quantityAvailable(address: { country: $country1 })
            quantityUS: quantityAvailable(address: { country: $country2 })
            quantityNoAddress: quantityAvailable
        }
    }
    """

    variant = variant_with_many_stocks_different_shipping_zones
    stock_map = {}
    for stock in variant.stocks.all():
        country = stock.warehouse.shipping_zones.get().countries[0]
        stock_map[country.code] = stock.quantity

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
        "country1": "PL",
        "country2": "US",
    }
    response = api_client.post_graphql(
        query,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["productVariant"]["quantityPL"] == stock_map["PL"]
    assert content["data"]["productVariant"]["quantityUS"] == stock_map["US"]

    # when country is not provided, should return max value of all available stock
    # quantities
    assert content["data"]["productVariant"]["quantityNoAddress"] == max(
        stock_map.values()
    )


def test_stock_quantity_is_max_from_all_warehouses_without_provided_country(
    api_client, channel_USD, variant_with_many_stocks_different_shipping_zones
):
    query = """
    query ProductVariant($id: ID!, $channel: String!) {
        productVariant(id: $id, channel: $channel) {
            quantityAvailable
        }
    }
    """

    variant = variant_with_many_stocks_different_shipping_zones
    max_warehouse_quantity = max([stock.quantity for stock in variant.stocks.all()])

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    assert (
        content["data"]["productVariant"]["quantityAvailable"] == max_warehouse_quantity
    )


def test_stock_quantity_is_sum_of_quantities_from_warehouses_that_support_country(
    api_client,
    address,
    channel_USD,
    shipping_zone,
    variant_with_many_stocks_different_shipping_zones,
):
    query = """
    query ProductVariant($id: ID!, $channel: String!, $country: CountryCode) {
        productVariant(id: $id, channel: $channel) {
            quantityAvailable(address: { country: $country })
        }
    }
    """

    variant = variant_with_many_stocks_different_shipping_zones

    # Create another warehouse with a different shipping zone that supports PL. As
    # a result there should be two shipping zones and two warehouses that support PL.
    stocks = variant.stocks.for_channel_and_country(channel_USD.slug, "PL")
    warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="WarehousePL",
        slug="warehousePL",
        email="warehousePL@example.com",
    )
    warehouse.shipping_zones.add(shipping_zone)
    warehouse.channels.add(channel_USD)
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=10)

    stocks = variant.stocks.for_channel_and_country(channel_USD.slug, "PL")
    sum_quantities = sum([stock.quantity for stock in stocks])

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
        "country": "PL",
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    assert content["data"]["productVariant"]["quantityAvailable"] == sum_quantities
