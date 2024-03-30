import graphene
import pytest
from django.contrib.sites.models import Site
from measurement.measures import Weight

from .....attribute import AttributeInputType, AttributeType
from .....attribute.models import Attribute
from .....core.taxes import TaxType
from .....core.units import WeightUnits
from .....plugins.manager import PluginsManager
from .....product import ProductTypeKind
from .....product.models import Product, ProductChannelListing, ProductType
from ....tests.utils import get_graphql_content, get_graphql_content_from_response
from ...enums import VariantAttributeScope

PRODUCT_TYPE_QUERY = """
    query getProductType(
        $id: ID!, $variantSelection: VariantAttributeScope, $channel: String
    ) {
        productType(id: $id) {
            name
            variantAttributes(variantSelection: $variantSelection) {
                slug
            }
            products(first: 20, channel:$channel) {
                totalCount
                edges {
                    node {
                        name
                    }
                }
            }
            taxType {
                taxCode
                description
            }
        }
    }
"""


def test_product_type_query(
    user_api_client,
    staff_api_client,
    product_type,
    file_attribute_with_file_input_type_without_values,
    product,
    permission_manage_products,
    monkeypatch,
    channel_USD,
):
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(code="123", description="Standard Taxes"),
    )

    query = PRODUCT_TYPE_QUERY

    no_products = Product.objects.count()
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    product_type.variant_attributes.add(
        file_attribute_with_file_input_type_without_values
    )
    variant_attributes_count = product_type.variant_attributes.count()

    variables = {
        "id": graphene.Node.to_global_id("ProductType", product_type.id),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]["products"]["totalCount"] == no_products - 1

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]["products"]["totalCount"] == no_products
    assert data["productType"]["taxType"]["taxCode"] == "123"
    assert data["productType"]["taxType"]["description"] == "Standard Taxes"
    assert len(data["productType"]["variantAttributes"]) == variant_attributes_count


def test_product_type_query_invalid_id(
    staff_api_client, product, channel_USD, permission_manage_products
):
    product_type_id = "'"
    variables = {
        "id": product_type_id,
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(PRODUCT_TYPE_QUERY, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"]
        == f"Invalid ID: {product_type_id}. Expected: ProductType."
    )
    assert content["data"]["productType"] is None


def test_product_type_query_object_with_given_id_does_not_exist(
    staff_api_client, product, channel_USD, permission_manage_products
):
    product_type_id = graphene.Node.to_global_id("ProductType", -1)
    variables = {
        "id": product_type_id,
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(PRODUCT_TYPE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["productType"] is None


def test_product_type_query_with_invalid_object_type(
    staff_api_client, product, channel_USD, permission_manage_products
):
    product_type_id = graphene.Node.to_global_id("Product", product.product_type.pk)
    variables = {
        "id": product_type_id,
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(PRODUCT_TYPE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["productType"] is None


@pytest.mark.parametrize(
    "variant_selection",
    [
        VariantAttributeScope.ALL.name,
        VariantAttributeScope.VARIANT_SELECTION.name,
        VariantAttributeScope.NOT_VARIANT_SELECTION.name,
    ],
)
def test_product_type_query_only_variant_selections_value_set(
    variant_selection,
    user_api_client,
    staff_api_client,
    product_type,
    file_attribute_with_file_input_type_without_values,
    author_page_attribute,
    product_type_page_reference_attribute,
    product,
    permission_manage_products,
    monkeypatch,
    channel_USD,
):
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(code="123", description="Standard Taxes"),
    )
    query = PRODUCT_TYPE_QUERY

    no_products = Product.objects.count()
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    product_type.variant_attributes.add(
        file_attribute_with_file_input_type_without_values,
        author_page_attribute,
        product_type_page_reference_attribute,
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductType", product_type.id),
        "variantSelection": variant_selection,
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]["products"]["totalCount"] == no_products - 1

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]["products"]["totalCount"] == no_products
    assert data["productType"]["taxType"]["taxCode"] == "123"
    assert data["productType"]["taxType"]["description"] == "Standard Taxes"

    if variant_selection == VariantAttributeScope.VARIANT_SELECTION.name:
        assert (
            len(data["productType"]["variantAttributes"])
            == product_type.variant_attributes.filter(
                input_type=AttributeInputType.DROPDOWN, type=AttributeType.PRODUCT_TYPE
            ).count()
        )
    elif variant_selection == VariantAttributeScope.NOT_VARIANT_SELECTION.name:
        assert (
            len(data["productType"]["variantAttributes"])
            == product_type.variant_attributes.exclude(
                input_type=AttributeInputType.DROPDOWN, type=AttributeType.PRODUCT_TYPE
            ).count()
        )
    else:
        assert (
            len(data["productType"]["variantAttributes"])
            == product_type.variant_attributes.count()
        )


PRODUCT_TYPE_QUERY_ASSIGNED_VARIANT_ATTRIBUTES = """
    query getProductType(
        $id: ID!, $variantSelection: VariantAttributeScope, $channel: String
    ) {
        productType(id: $id) {
            name
            assignedVariantAttributes(variantSelection: $variantSelection) {
                attribute {
                    slug
                }
                variantSelection
            }
            products(first: 20, channel:$channel) {
                totalCount
                edges {
                    node {
                        name
                    }
                }
            }
            taxType {
                taxCode
                description
            }
        }
    }
"""


@pytest.mark.parametrize(
    "variant_selection",
    [
        VariantAttributeScope.ALL.name,
        VariantAttributeScope.VARIANT_SELECTION.name,
        VariantAttributeScope.NOT_VARIANT_SELECTION.name,
    ],
)
def test_product_type_query_only_assigned_variant_selections_value_set(
    variant_selection,
    user_api_client,
    staff_api_client,
    product_type,
    file_attribute_with_file_input_type_without_values,
    author_page_attribute,
    product_type_page_reference_attribute,
    product,
    permission_manage_products,
    monkeypatch,
    channel_USD,
):
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(code="123", description="Standard Taxes"),
    )
    query = PRODUCT_TYPE_QUERY_ASSIGNED_VARIANT_ATTRIBUTES

    no_products = Product.objects.count()
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    product_type.variant_attributes.add(
        file_attribute_with_file_input_type_without_values,
        author_page_attribute,
        product_type_page_reference_attribute,
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductType", product_type.id),
        "variantSelection": variant_selection,
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]["products"]["totalCount"] == no_products - 1

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]["products"]["totalCount"] == no_products
    assert data["productType"]["taxType"]["taxCode"] == "123"
    assert data["productType"]["taxType"]["description"] == "Standard Taxes"

    if variant_selection == VariantAttributeScope.VARIANT_SELECTION.name:
        assert (
            len(data["productType"]["assignedVariantAttributes"])
            == product_type.variant_attributes.filter(
                input_type=AttributeInputType.DROPDOWN, type=AttributeType.PRODUCT_TYPE
            ).count()
        )
        assert all(
            assign["variantSelection"]
            for assign in data["productType"]["assignedVariantAttributes"]
        )
    elif variant_selection == VariantAttributeScope.NOT_VARIANT_SELECTION.name:
        assert (
            len(data["productType"]["assignedVariantAttributes"])
            == product_type.variant_attributes.exclude(
                input_type=AttributeInputType.DROPDOWN, type=AttributeType.PRODUCT_TYPE
            ).count()
        )
        assert not any(
            assign["variantSelection"]
            for assign in data["productType"]["assignedVariantAttributes"]
        )

    else:
        assert (
            len(data["productType"]["assignedVariantAttributes"])
            == product_type.variant_attributes.count()
        )


QUERY_AVAILABLE_ATTRIBUTES = """
    query(
        $productTypeId:ID!, $filters: AttributeFilterInput, $where: AttributeWhereInput
    ) {
      productType(id: $productTypeId) {
        availableAttributes(first: 10, filter: $filters, where: $where) {
          edges {
            node {
              id
              slug
            }
          }
        }
      }
    }
"""


def test_product_type_get_unassigned_product_type_attributes(
    staff_api_client, permission_manage_products
):
    query = QUERY_AVAILABLE_ATTRIBUTES
    target_product_type, ignored_product_type = ProductType.objects.bulk_create(
        [
            ProductType(name="Type 1", slug="type-1"),
            ProductType(name="Type 2", slug="type-2"),
        ]
    )

    unassigned_attributes = list(
        Attribute.objects.bulk_create(
            [
                Attribute(slug="size", name="Size", type=AttributeType.PRODUCT_TYPE),
                Attribute(
                    slug="weight", name="Weight", type=AttributeType.PRODUCT_TYPE
                ),
                Attribute(
                    slug="thickness", name="Thickness", type=AttributeType.PRODUCT_TYPE
                ),
            ]
        )
    )

    unassigned_page_attributes = list(
        Attribute.objects.bulk_create(
            [
                Attribute(slug="length", name="Length", type=AttributeType.PAGE_TYPE),
                Attribute(slug="width", name="Width", type=AttributeType.PAGE_TYPE),
            ]
        )
    )

    assigned_attributes = list(
        Attribute.objects.bulk_create(
            [
                Attribute(slug="color", name="Color", type=AttributeType.PRODUCT_TYPE),
                Attribute(slug="type", name="Type", type=AttributeType.PRODUCT_TYPE),
            ]
        )
    )

    # Ensure that assigning them to another product type
    # doesn't return an invalid response
    ignored_product_type.product_attributes.add(*unassigned_attributes)
    ignored_product_type.product_attributes.add(*unassigned_page_attributes)

    # Assign the other attributes to the target product type
    target_product_type.product_attributes.add(*assigned_attributes)

    gql_unassigned_attributes = get_graphql_content(
        staff_api_client.post_graphql(
            query,
            {
                "productTypeId": graphene.Node.to_global_id(
                    "ProductType", target_product_type.pk
                )
            },
            permissions=[permission_manage_products],
        )
    )["data"]["productType"]["availableAttributes"]["edges"]

    assert len(gql_unassigned_attributes) == len(
        unassigned_attributes
    ), gql_unassigned_attributes

    received_ids = sorted(attr["node"]["id"] for attr in gql_unassigned_attributes)
    expected_ids = sorted(
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in unassigned_attributes
    )

    assert received_ids == expected_ids


def test_product_type_filter_unassigned_attributes(
    staff_api_client, permission_manage_products, product_type_attribute_list
):
    expected_attribute = product_type_attribute_list[0]
    query = QUERY_AVAILABLE_ATTRIBUTES
    product_type = ProductType.objects.create(
        name="Empty Type", kind=ProductTypeKind.NORMAL
    )
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    filters = {"search": expected_attribute.name}

    found_attributes = get_graphql_content(
        staff_api_client.post_graphql(
            query,
            {"productTypeId": product_type_id, "filters": filters},
            permissions=[permission_manage_products],
        )
    )["data"]["productType"]["availableAttributes"]["edges"]

    assert len(found_attributes) == 1

    _, attribute_id = graphene.Node.from_global_id(found_attributes[0]["node"]["id"])
    assert attribute_id == str(expected_attribute.pk)


def test_product_type_where_filter_unassigned_attributes(
    staff_api_client, permission_manage_products, product_type_attribute_list
):
    expected_attribute = product_type_attribute_list[0]
    query = QUERY_AVAILABLE_ATTRIBUTES
    product_type = ProductType.objects.create(
        name="Empty Type", kind=ProductTypeKind.NORMAL
    )
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    where = {"name": {"eq": expected_attribute.name}}

    found_attributes = get_graphql_content(
        staff_api_client.post_graphql(
            query,
            {"productTypeId": product_type_id, "where": where},
            permissions=[permission_manage_products],
        )
    )["data"]["productType"]["availableAttributes"]["edges"]

    assert len(found_attributes) == 1

    _, attribute_id = graphene.Node.from_global_id(found_attributes[0]["node"]["id"])
    assert attribute_id == str(expected_attribute.pk)


QUERY_PRODUCT_TYPE = """
    query ($id: ID!){
        productType(
            id: $id,
        ) {
            id
            name
            weight {
                unit
                value
            }
        }
    }
"""


def test_product_type_query_by_id_weight_returned_in_default_unit(
    user_api_client, product_type, site_settings
):
    # given
    product_type.weight = Weight(kg=10)
    product_type.save(update_fields=["weight"])

    site_settings.default_weight_unit = WeightUnits.OZ
    site_settings.save(update_fields=["default_weight_unit"])
    Site.objects.clear_cache()

    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_PRODUCT_TYPE, variables=variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["productType"]
    assert product_data is not None
    assert product_data["name"] == product_type.name
    assert product_data["weight"]["value"] == round(product_type.weight.oz, 3)
    assert product_data["weight"]["unit"] == WeightUnits.OZ.upper()


def test_query_product_type_for_federation(api_client, product, channel_USD):
    product_type = product.product_type
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    variables = {
        "representations": [
            {
                "__typename": "ProductType",
                "id": product_type_id,
            },
        ],
    }
    query = """
      query GetProductTypeInFederation($representations: [_Any]) {
        _entities(representations: $representations) {
          __typename
          ... on ProductType {
            id
            name
          }
        }
      }
    """

    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "ProductType",
            "id": product_type_id,
            "name": product_type.name,
        }
    ]


PRODUCT_TYPE_TAX_CLASS_QUERY = """
    query getProductType($id: ID!) {
        productType(id: $id) {
            id
            taxClass {
                id
            }
        }
    }
"""


def test_product_type_tax_class_query_by_app(
    app_api_client,
    product_type,
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("ProductType", product_type.id),
    }

    # when
    response = app_api_client.post_graphql(PRODUCT_TYPE_TAX_CLASS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]
    assert data["productType"]["id"]
    assert data["productType"]["taxClass"]["id"]


def test_product_type_tax_class_query_by_staff(staff_api_client, product_type):
    # given
    variables = {
        "id": graphene.Node.to_global_id("ProductType", product_type.id),
    }

    # when
    response = staff_api_client.post_graphql(PRODUCT_TYPE_TAX_CLASS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]
    assert data["productType"]["id"]
    assert data["productType"]["taxClass"]["id"]


QUERY_PRODUCT_TYPE_ATTRIBUTES = """
    query ProductType($id: ID!) {
        productType(id: $id) {
            id
            productAttributes {
                id
                slug
            }
            variantAttributes {
                id
                slug
            }
            assignedVariantAttributes {
                attribute {
                    id
                    slug
                }
            }
        }
    }
"""


def test_product_type_attribute_not_visible_in_storefront_for_customer_is_not_returned(
    user_api_client, product_type
):
    # given
    prod_attribute = product_type.product_attributes.first()
    prod_attribute.visible_in_storefront = False
    prod_attribute.save(update_fields=["visible_in_storefront"])
    visible_prod_attrs_count = product_type.product_attributes.filter(
        visible_in_storefront=True
    ).count()

    variant_attribute = product_type.variant_attributes.first()
    variant_attribute.visible_in_storefront = False
    variant_attribute.save(update_fields=["visible_in_storefront"])
    visible_variant_attrs_count = product_type.variant_attributes.filter(
        visible_in_storefront=True
    ).count()

    # when
    variables = {
        "id": graphene.Node.to_global_id("ProductType", product_type.pk),
    }
    response = user_api_client.post_graphql(
        QUERY_PRODUCT_TYPE_ATTRIBUTES,
        variables,
    )

    # then
    content = get_graphql_content(response)

    assert (
        len(content["data"]["productType"]["productAttributes"])
        == visible_prod_attrs_count
    )
    assert (
        len(content["data"]["productType"]["variantAttributes"])
        == visible_variant_attrs_count
    )
    assert (
        len(content["data"]["productType"]["assignedVariantAttributes"])
        == visible_variant_attrs_count
    )

    prod_attr_data = {
        "id": graphene.Node.to_global_id("Attribute", prod_attribute.pk),
        "slug": prod_attribute.slug,
    }
    assert prod_attr_data not in content["data"]["productType"]["productAttributes"]

    variant_attr_data = {
        "id": graphene.Node.to_global_id("Attribute", variant_attribute.pk),
        "slug": variant_attribute.slug,
    }
    assert variant_attr_data not in content["data"]["productType"]["variantAttributes"]

    assert {"attribute": variant_attr_data} not in content["data"]["productType"][
        "assignedVariantAttributes"
    ]


def test_product_type_attribute_visible_in_storefront_for_customer_is_returned(
    user_api_client, product_type
):
    # given
    prod_attribute = product_type.product_attributes.first()
    prod_attribute.visible_in_storefront = True
    prod_attribute.save(update_fields=["visible_in_storefront"])
    visible_prod_attrs_count = product_type.product_attributes.filter(
        visible_in_storefront=True
    ).count()

    variant_attribute = product_type.variant_attributes.first()
    variant_attribute.visible_in_storefront = True
    variant_attribute.save(update_fields=["visible_in_storefront"])
    visible_variant_attrs_count = product_type.variant_attributes.filter(
        visible_in_storefront=True
    ).count()

    # when
    variables = {
        "id": graphene.Node.to_global_id("ProductType", product_type.pk),
    }
    response = user_api_client.post_graphql(
        QUERY_PRODUCT_TYPE_ATTRIBUTES,
        variables,
    )

    # then
    content = get_graphql_content(response)

    assert (
        len(content["data"]["productType"]["productAttributes"])
        == visible_prod_attrs_count
    )
    assert (
        len(content["data"]["productType"]["variantAttributes"])
        == visible_variant_attrs_count
    )
    assert (
        len(content["data"]["productType"]["assignedVariantAttributes"])
        == visible_variant_attrs_count
    )

    prod_attr_data = {
        "id": graphene.Node.to_global_id("Attribute", prod_attribute.pk),
        "slug": prod_attribute.slug,
    }
    assert prod_attr_data in content["data"]["productType"]["productAttributes"]

    variant_attr_data = {
        "id": graphene.Node.to_global_id("Attribute", variant_attribute.pk),
        "slug": variant_attribute.slug,
    }
    assert variant_attr_data in content["data"]["productType"]["variantAttributes"]

    assert {"attribute": variant_attr_data} in content["data"]["productType"][
        "assignedVariantAttributes"
    ]


@pytest.mark.parametrize("visible_in_storefront", [False, True])
def test_product_type_attribute_visible_in_storefront_for_staff_is_always_returned(
    visible_in_storefront,
    staff_api_client,
    product_type,
    permission_manage_products,
):
    # given
    prod_attribute = product_type.product_attributes.first()
    prod_attribute.visible_in_storefront = visible_in_storefront
    prod_attribute.save(update_fields=["visible_in_storefront"])
    visible_prod_attrs_count = product_type.product_attributes.filter(
        visible_in_storefront=visible_in_storefront
    ).count()

    variant_attribute = product_type.variant_attributes.first()
    variant_attribute.visible_in_storefront = visible_in_storefront
    variant_attribute.save(update_fields=["visible_in_storefront"])
    visible_variant_attrs_count = product_type.variant_attributes.filter(
        visible_in_storefront=visible_in_storefront
    ).count()

    # when
    variables = {
        "id": graphene.Node.to_global_id("ProductType", product_type.pk),
    }
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_TYPE_ATTRIBUTES,
        variables,
    )

    # then
    content = get_graphql_content(response)

    assert (
        len(content["data"]["productType"]["productAttributes"])
        == visible_prod_attrs_count
    )
    assert (
        len(content["data"]["productType"]["variantAttributes"])
        == visible_variant_attrs_count
    )
    assert (
        len(content["data"]["productType"]["assignedVariantAttributes"])
        == visible_variant_attrs_count
    )

    prod_attr_data = {
        "id": graphene.Node.to_global_id("Attribute", prod_attribute.pk),
        "slug": prod_attribute.slug,
    }
    assert prod_attr_data in content["data"]["productType"]["productAttributes"]

    variant_attr_data = {
        "id": graphene.Node.to_global_id("Attribute", variant_attribute.pk),
        "slug": variant_attribute.slug,
    }
    assert variant_attr_data in content["data"]["productType"]["variantAttributes"]

    assert {"attribute": variant_attr_data} in content["data"]["productType"][
        "assignedVariantAttributes"
    ]
