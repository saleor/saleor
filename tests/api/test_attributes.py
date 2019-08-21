from typing import Union

import graphene
import pytest
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.template.defaultfilters import slugify
from graphene.utils.str_converters import to_camel_case

from saleor.graphql.core.utils import snake_to_camel_case
from saleor.graphql.product.enums import AttributeTypeEnum, AttributeValueType
from saleor.graphql.product.mutations.attributes import validate_value_is_unique
from saleor.graphql.product.types.attributes import resolve_attribute_value_type
from saleor.graphql.product.types.products import resolve_attribute_list
from saleor.graphql.product.utils import attributes_to_json
from saleor.product import AttributeInputType
from saleor.product.models import (
    Attribute,
    AttributeProduct,
    AttributeValue,
    AttributeVariant,
    Category,
    ProductType,
)
from tests.api.utils import get_graphql_content


def test_validate_value_is_unique(color_attribute):
    value = color_attribute.values.first()

    # a new value but with existing slug should raise an error
    with pytest.raises(ValidationError):
        validate_value_is_unique(color_attribute, AttributeValue(slug=value.slug))

    # a new value with a new slug should pass
    validate_value_is_unique(
        color_attribute, AttributeValue(slug="spanish-inquisition")
    )

    # value that already belongs to the attribute shouldn't be taken into account
    validate_value_is_unique(color_attribute, value)


def test_attributes_to_json(product, color_attribute, size_attribute):
    attribute_values_count = AttributeValue.objects.count()

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    color_value = color_attribute.values.first()

    # test transforming slugs of existing attributes to IDs
    input_data = [{"id": attribute_id, "values": [color_value.slug]}]
    attrs_qs = product.product_type.product_attributes.all()
    ids = attributes_to_json(input_data, attrs_qs)
    assert str(color_attribute.pk) in ids
    assert ids[str(color_attribute.pk)] == [str(color_value.pk)]
    assert (
        AttributeValue.objects.count() == attribute_values_count
    ), "No new values should been created"

    # test creating a new attribute value
    input_data = [{"id": attribute_id, "values": ["Space Grey"]}]
    ids = attributes_to_json(input_data, attrs_qs)
    new_value = AttributeValue.objects.get(slug="space-grey")
    attribute_values_count += 1
    assert str(color_attribute.pk) in ids
    assert ids[str(color_attribute.pk)] == [str(new_value.pk)]

    # test passing the newly created value by slug
    input_data = [{"id": attribute_id, "values": ["space-grey"]}]
    attributes_to_json(input_data, attrs_qs)
    assert (
        AttributeValue.objects.count() == attribute_values_count
    ), "Only one new value should have been created"


# WARNING: Passing by slug will be dropped in a future release
# This test can be safely removed on the field is dropped.
def test_attributes_to_json_passing_by_slug(product, color_attribute):
    color_value = color_attribute.values.first()

    # test transforming slugs of existing attributes to IDs
    input_data = [{"slug": color_attribute.slug, "values": [color_value.slug]}]
    attrs_qs = product.product_type.product_attributes.all()
    ids = attributes_to_json(input_data, attrs_qs)
    assert str(color_attribute.pk) in ids
    assert ids[str(color_attribute.pk)] == [str(color_value.pk)]

    # test creating a new attribute value
    input_data = [{"slug": color_attribute.slug, "values": ["Space Grey"]}]
    ids = attributes_to_json(input_data, attrs_qs)
    new_value = AttributeValue.objects.get(slug="space-grey")
    assert str(color_attribute.pk) in ids
    assert ids[str(color_attribute.pk)] == [str(new_value.pk)]

    # test passing an attribute that doesn't belong to this product raises
    # an error
    input_data = [{"slug": "no-existing", "values": ["not-a-value"]}]
    with pytest.raises(ValueError) as exc:
        attributes_to_json(input_data, attrs_qs)
    assert exc.value.args == (
        "The given attribute doesn't belong to given product type.",
    )


@pytest.mark.parametrize("input", ([{"slug": "color", "values": []}], []))
def test_attributes_to_json_missing_required_value(product, color_attribute, input):
    # A value is required
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    # test transforming slugs of existing attributes to IDs
    attrs_qs = product.product_type.product_attributes.all()

    with pytest.raises(ValueError) as exc:
        attributes_to_json(input, attrs_qs)
    assert exc.value.args == ("color expects a value but none were given",)


def test_attributes_to_json_id_not_in_product_type(product, size_attribute):
    attrs_qs = product.product_type.product_attributes.all()

    # Pass an id not belonging to the product type
    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", size_attribute.pk),
            "values": ["a-value"],
        }
    ]
    with pytest.raises(ValueError) as exc:
        attributes_to_json(input_data, attrs_qs)
    assert exc.value.args == (
        "The given attribute doesn't belong to given product type.",
    )


def test_attributes_to_json_invalid_id_type(product):
    attrs_qs = product.product_type.product_attributes.all()
    invalid_id = graphene.Node.to_global_id("Invalid", 1)

    # Pass an id of invalid type
    input_data = [{"id": invalid_id, "values": ["a-value"]}]
    with pytest.raises(ValueError) as exc:
        attributes_to_json(input_data, attrs_qs)
    assert exc.value.args == (f"Couldn't resolve to a node: {invalid_id}",)


def test_attributes_to_json_without_values(product, color_attribute):
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    input_data = [{"id": attribute_id, "values": []}]
    attrs_qs = product.product_type.product_attributes.all()

    # The attribute should be ignored and raise no error as the value is not required
    assert not attributes_to_json(input_data, attrs_qs)


def test_attributes_to_json_duplicated_slug(product, color_attribute, size_attribute):
    # It's possible to have a value with the same slug but for a different attribute.
    # Ensure that `attributes_to_json` works in that case.

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    color_value = color_attribute.values.first()

    # Create a fake duplicated value.
    AttributeValue.objects.create(
        slug=color_value.slug, name="Duplicated value", attribute=size_attribute
    )

    input_data = [{"id": attribute_id, "values": [color_value.slug]}]
    attrs_qs = product.product_type.product_attributes.all()
    ids = attributes_to_json(input_data, attrs_qs)
    assert str(color_attribute.pk) in ids
    assert ids[str(color_attribute.pk)] == [str(color_value.pk)]


def test_attributes_to_json_missing_value_getter_raises_error(product):
    # test transforming slugs of existing attributes to IDs
    input_data = [{"values": []}]
    attrs_qs = product.product_type.product_attributes.all()

    with pytest.raises(ValueError) as exc:
        assert not attributes_to_json(input_data, attrs_qs)

    assert exc.value.args == ("The value ID or slug was not provided",)


def test_get_single_attribute_by_pk(user_api_client, color_attribute_without_values):
    attribute_gql_id = graphene.Node.to_global_id(
        "Attribute", color_attribute_without_values.id
    )
    query = """
    query($id: ID!) {
        attribute(id: $id) {
            id
            slug
        }
    }
    """
    content = get_graphql_content(
        user_api_client.post_graphql(query, {"id": attribute_gql_id})
    )

    assert content["data"]["attribute"], "Should have found an attribute"
    assert content["data"]["attribute"]["id"] == attribute_gql_id
    assert content["data"]["attribute"]["slug"] == color_attribute_without_values.slug


QUERY_ATTRIBUTES = """
    query {
        attributes(first: 20) {
            edges {
                node {
                    id
                    name
                    slug
                    values {
                        id
                        name
                        slug
                    }
                }
            }
        }
    }
"""


def test_attributes_query(user_api_client, product):
    attributes = Attribute.objects
    query = QUERY_ATTRIBUTES
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    attributes_data = content["data"]["attributes"]["edges"]
    assert attributes_data
    assert len(attributes_data) == attributes.count()


def test_attributes_query_hidden_attribute(user_api_client, product, color_attribute):
    query = QUERY_ATTRIBUTES

    # hide the attribute
    color_attribute.visible_in_storefront = False
    color_attribute.save(update_fields=["visible_in_storefront"])

    attribute_count = Attribute.objects.get_visible_to_user(
        user_api_client.user
    ).count()
    assert attribute_count == 1

    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    attributes_data = content["data"]["attributes"]["edges"]
    assert len(attributes_data) == attribute_count


def test_attributes_query_hidden_attribute_as_staff_user(
    staff_api_client, product, color_attribute, permission_manage_products
):
    query = QUERY_ATTRIBUTES

    # hide the attribute
    color_attribute.visible_in_storefront = False
    color_attribute.save(update_fields=["visible_in_storefront"])

    attribute_count = Attribute.objects.all().count()

    # The user doesn't have the permission yet to manage products,
    # the user shouldn't be able to see the hidden attributes
    assert Attribute.objects.get_visible_to_user(staff_api_client.user).count() == 1

    # The user should now be able to see the attributes
    staff_api_client.user.user_permissions.add(permission_manage_products)

    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    attributes_data = content["data"]["attributes"]["edges"]
    assert len(attributes_data) == attribute_count


QUERY_PRODUCT_ATTRIBUTES = """
    {
      products(first: 1) {
        edges {
          node {
            attributes {
              attribute {
                name
              }
            }
          }
        }
      }
    }
"""


def test_resolve_product_attributes_with_hidden(
    user_api_client, product, color_attribute
):
    query = QUERY_PRODUCT_ATTRIBUTES

    # Hide one attribute from the storefront
    color_attribute.visible_in_storefront = False
    color_attribute.save(update_fields=["visible_in_storefront"])

    gql_attrs = get_graphql_content(user_api_client.post_graphql(query))["data"][
        "products"
    ]["edges"][0]["node"]["attributes"]
    assert len(gql_attrs) == len(product.attributes) - 1


def test_resolve_product_attributes_with_hidden_as_staff_user(
    staff_api_client, product, color_attribute, permission_manage_products
):
    query = QUERY_PRODUCT_ATTRIBUTES

    # Hide one attribute from the storefront
    color_attribute.visible_in_storefront = False
    color_attribute.save(update_fields=["visible_in_storefront"])

    # Add proper permissions
    staff_api_client.user.user_permissions.add(permission_manage_products)

    gql_attrs = get_graphql_content(staff_api_client.post_graphql(query))["data"][
        "products"
    ]["edges"][0]["node"]["attributes"]
    assert len(gql_attrs) == len(product.attributes)


QUERY_VARIANT_ATTRIBUTES = """
    {
      products(first: 1) {
        edges {
          node {
            variants {
              attributes {
                attribute {
                  name
                }
              }
            }
          }
        }
      }
    }
"""


def test_resolve_variant_attributes_with_hidden(
    user_api_client, product, size_attribute
):
    query = QUERY_VARIANT_ATTRIBUTES

    # Hide one attribute from the storefront
    size_attribute.visible_in_storefront = False
    size_attribute.save(update_fields=["visible_in_storefront"])

    gql_attrs = get_graphql_content(user_api_client.post_graphql(query))["data"][
        "products"
    ]["edges"][0]["node"]["variants"][0]["attributes"]
    assert len(gql_attrs) == len(product.variants.first().attributes) - 1


def test_resolve_variant_attributes_with_hidden_as_staff_user(
    staff_api_client, product, size_attribute, permission_manage_products
):
    query = QUERY_VARIANT_ATTRIBUTES

    # Hide one attribute from the storefront
    size_attribute.visible_in_storefront = False
    size_attribute.save(update_fields=["visible_in_storefront"])

    # Add proper permissions
    staff_api_client.user.user_permissions.add(permission_manage_products)

    gql_attrs = get_graphql_content(staff_api_client.post_graphql(query))["data"][
        "products"
    ]["edges"][0]["node"]["variants"][0]["attributes"]
    assert len(gql_attrs) == len(product.variants.first().attributes)


def test_attributes_in_category_query(user_api_client, product):
    category = Category.objects.first()
    query = """
    query {
        attributes(inCategory: "%(category_id)s", first: 20) {
            edges {
                node {
                    id
                    name
                    slug
                }
            }
        }
    }
    """ % {
        "category_id": graphene.Node.to_global_id("Category", category.id)
    }
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    attributes_data = content["data"]["attributes"]["edges"]
    assert len(attributes_data) == Attribute.objects.count()


def test_attributes_in_collection_query(user_api_client, collection):
    product_types = set(
        collection.products.all().values_list("product_type_id", flat=True)
    )
    expected_attrs = Attribute.objects.filter(
        Q(attributeproduct__product_type_id__in=product_types)
        | Q(attributevariant__product_type_id__in=product_types)
    )

    query = """
    query {
        attributes(inCollection: "%(collection_id)s", first: 20) {
            edges {
                node {
                    id
                    name
                    slug
                }
            }
        }
    }
    """ % {
        "collection_id": graphene.Node.to_global_id("Collection", collection.pk)
    }
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    attributes_data = content["data"]["attributes"]["edges"]
    assert len(attributes_data) == len(expected_attrs)


CREATE_ATTRIBUTES_QUERY = """
    mutation createAttribute($name: String!, $values: [AttributeValueCreateInput]) {
        attributeCreate(input: {name: $name, values: $values}) {
            errors {
                field
                message
            }
            attribute {
                name
                slug
                values {
                    name
                    slug
                }
                productTypes(first: 10) {
                    edges {
                        node {
                            id
                        }
                    }
                }
            }
        }
    }
"""


def test_create_attribute_and_attribute_values(
    staff_api_client, permission_manage_products
):
    query = CREATE_ATTRIBUTES_QUERY

    attribute_name = "Example name"
    name = "Value name"
    variables = {"name": attribute_name, "values": [{"name": name, "value": "#1231"}]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert not content["data"]["attributeCreate"]["errors"]
    data = content["data"]["attributeCreate"]

    # Check if the attribute was correctly created
    assert data["attribute"]["name"] == attribute_name
    assert data["attribute"]["slug"] == slugify(
        attribute_name
    ), "The default slug should be the slugified name"
    assert (
        data["attribute"]["productTypes"]["edges"] == []
    ), "The attribute should not have been assigned to a product type"

    # Check if the attribute values were correctly created
    assert len(data["attribute"]["values"]) == 1
    assert data["attribute"]["values"][0]["name"] == name
    assert data["attribute"]["values"][0]["slug"] == slugify(name)


@pytest.mark.parametrize(
    "input_slug, expected_slug, expected_error",
    (
        ("my-slug", "my-slug", []),
        (None, "my-name", []),
        (
            "",
            None,
            [{"field": "slug", "message": "The attribute's slug cannot be blank."}],
        ),
    ),
)
def test_create_attribute_with_given_slug(
    staff_api_client,
    permission_manage_products,
    input_slug,
    expected_slug,
    expected_error,
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    query = """
        mutation createAttribute(
            $name: String!, $slug: String) {
        attributeCreate(input: {name: $name, slug: $slug}) {
            errors {
                field
                message
            }
            attribute {
                slug
            }
        }
    }
    """

    attribute_name = "My Name"
    variables = {"name": attribute_name, "slug": input_slug}
    content = get_graphql_content(staff_api_client.post_graphql(query, variables))

    # Check if the error is as expected: null or something else
    assert content["data"]["attributeCreate"]["errors"] == expected_error

    # Check if the slug was correctly set if no error was expected
    if expected_error is None:
        assert content["data"]["attributeCreate"]["attribute"]["slug"] == expected_slug


@pytest.mark.parametrize(
    "name_1, name_2, error_msg",
    (
        ("Red color", "Red color", "Provided values are not unique."),
        ("Red color", "red color", "Provided values are not unique."),
    ),
)
def test_create_attribute_and_attribute_values_errors(
    staff_api_client,
    name_1,
    name_2,
    error_msg,
    permission_manage_products,
    product_type,
):
    query = CREATE_ATTRIBUTES_QUERY
    variables = {
        "name": "Example name",
        "values": [
            {"name": name_1, "value": "#1231"},
            {"name": name_2, "value": "#121"},
        ],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    errors = content["data"]["attributeCreate"]["errors"]
    assert errors
    assert errors[0]["field"] == "values"
    assert errors[0]["message"] == error_msg


UPDATE_ATTRIBUTE_QUERY = """
    mutation updateAttribute(
        $id: ID!, $name: String!, $addValues: [AttributeValueCreateInput]!,
        $removeValues: [ID]!) {
    attributeUpdate(
            id: $id,
            input: {
                name: $name, addValues: $addValues,
                removeValues: $removeValues}) {
        errors {
            field
            message
        }
        attribute {
            name
            slug
            values {
                name
                slug
            }
            productTypes(first: 10) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    }
}
"""


def test_update_attribute_name(
    staff_api_client, color_attribute, permission_manage_products
):
    query = UPDATE_ATTRIBUTE_QUERY
    attribute = color_attribute
    name = "Wings name"
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"name": name, "id": node_id, "addValues": [], "removeValues": []}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content["data"]["attributeUpdate"]
    assert data["attribute"]["name"] == name == attribute.name
    assert data["attribute"]["productTypes"]["edges"] == []


def test_update_attribute_remove_and_add_values(
    staff_api_client, color_attribute, permission_manage_products
):
    query = UPDATE_ATTRIBUTE_QUERY
    attribute = color_attribute
    name = "Wings name"
    attribute_value_name = "Red Color"
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    attribute_value_id = attribute.values.first().id
    value_id = graphene.Node.to_global_id("AttributeValue", attribute_value_id)
    variables = {
        "name": name,
        "id": node_id,
        "addValues": [{"name": attribute_value_name, "value": "#1231"}],
        "removeValues": [value_id],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content["data"]["attributeUpdate"]
    assert not data["errors"]
    assert data["attribute"]["name"] == name == attribute.name
    assert not attribute.values.filter(pk=attribute_value_id).exists()
    assert attribute.values.filter(name=attribute_value_name).exists()


def test_update_empty_attribute_and_add_values(
    staff_api_client, color_attribute_without_values, permission_manage_products
):
    query = UPDATE_ATTRIBUTE_QUERY
    attribute = color_attribute_without_values
    name = "Wings name"
    attribute_value_name = "Yellow Color"
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {
        "name": name,
        "id": node_id,
        "addValues": [{"name": attribute_value_name, "value": "#1231"}],
        "removeValues": [],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    attribute.refresh_from_db()
    assert attribute.values.count() == 1
    assert attribute.values.filter(name=attribute_value_name).exists()


@pytest.mark.parametrize(
    "name_1, name_2, error_msg",
    (
        ("Red color", "Red color", "Provided values are not unique."),
        ("Red color", "red color", "Provided values are not unique."),
    ),
)
def test_update_attribute_and_add_attribute_values_errors(
    staff_api_client,
    name_1,
    name_2,
    error_msg,
    color_attribute,
    permission_manage_products,
):
    query = UPDATE_ATTRIBUTE_QUERY
    attribute = color_attribute
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {
        "name": "Example name",
        "id": node_id,
        "removeValues": [],
        "addValues": [{"name": name_1, "value": "#1"}, {"name": name_2, "value": "#2"}],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    errors = content["data"]["attributeUpdate"]["errors"]
    assert errors
    assert errors[0]["field"] == "addValues"
    assert errors[0]["message"] == error_msg


def test_update_attribute_and_remove_others_attribute_value(
    staff_api_client, color_attribute, size_attribute, permission_manage_products
):
    query = UPDATE_ATTRIBUTE_QUERY
    attribute = color_attribute
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    size_attribute = size_attribute.values.first()
    attr_id = graphene.Node.to_global_id("AttributeValue", size_attribute.pk)
    variables = {
        "name": "Example name",
        "id": node_id,
        "slug": "example-slug",
        "addValues": [],
        "removeValues": [attr_id],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    errors = content["data"]["attributeUpdate"]["errors"]
    assert errors
    assert errors[0]["field"] == "removeValues"
    err_msg = "Value %s does not belong to this attribute." % str(size_attribute)
    assert errors[0]["message"] == err_msg


def test_delete_attribute(
    staff_api_client, color_attribute, permission_manage_products, product_type
):
    attribute = color_attribute
    query = """
    mutation deleteAttribute($id: ID!) {
        attributeDelete(id: $id) {
            errors {
                field
                message
            }
            attribute {
                id
            }
        }
    }
    """
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeDelete"]
    assert data["attribute"]["id"] == variables["id"]
    with pytest.raises(attribute._meta.model.DoesNotExist):
        attribute.refresh_from_db()


CREATE_ATTRIBUTE_VALUE_QUERY = """
    mutation createAttributeValue(
        $attributeId: ID!, $name: String!, $value: String) {
    attributeValueCreate(
        attribute: $attributeId, input: {name: $name, value: $value}) {
        errors {
            field
            message
        }
        attribute {
            values {
                name
            }
        }
        attributeValue {
            name
            type
            slug
            value
        }
    }
}
"""


def test_create_attribute_value(
    staff_api_client, color_attribute, permission_manage_products
):
    attribute = color_attribute
    query = CREATE_ATTRIBUTE_VALUE_QUERY
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    name = "test name"
    value = "test-string"
    variables = {"name": name, "value": value, "attributeId": attribute_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueCreate"]
    assert not data["errors"]

    attr_data = data["attributeValue"]
    assert attr_data["name"] == name
    assert attr_data["slug"] == slugify(name)
    assert attr_data["value"] == value
    assert attr_data["type"] == "STRING"
    assert name in [value["name"] for value in data["attribute"]["values"]]


def test_create_attribute_value_not_unique_name(
    staff_api_client, color_attribute, permission_manage_products
):
    attribute = color_attribute
    query = CREATE_ATTRIBUTE_VALUE_QUERY
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    value_name = attribute.values.first().name
    variables = {
        "name": value_name,
        "value": "test-string",
        "attributeId": attribute_id,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueCreate"]
    assert data["errors"]
    assert data["errors"][0]["message"]
    assert data["errors"][0]["field"] == "name"


UPDATE_ATTRIBUTE_VALUE_QUERY = """
mutation updateChoice(
        $id: ID!, $name: String!, $value: String) {
    attributeValueUpdate(
    id: $id, input: {name: $name, value: $value}) {
        errors {
            field
            message
        }
        attributeValue {
            name
            slug
            value
        }
        attribute {
            values {
                name
            }
        }
    }
}
"""


def test_update_attribute_value(
    staff_api_client, pink_attribute_value, permission_manage_products
):
    query = UPDATE_ATTRIBUTE_VALUE_QUERY
    value = pink_attribute_value
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    name = "Crimson name"
    variables = {"name": name, "value": "#RED", "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert data["attributeValue"]["name"] == name == value.name
    assert data["attributeValue"]["slug"] == slugify(name)
    assert name in [value["name"] for value in data["attribute"]["values"]]


def test_update_attribute_value_name_not_unique(
    staff_api_client, pink_attribute_value, permission_manage_products
):
    query = UPDATE_ATTRIBUTE_VALUE_QUERY
    value = pink_attribute_value.attribute.values.create(
        name="Example Name", slug="example-name", value="#RED"
    )
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    variables = {"name": pink_attribute_value.name, "value": "#RED", "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    assert data["errors"]
    assert data["errors"][0]["message"]
    assert data["errors"][0]["field"] == "name"


def test_update_same_attribute_value(
    staff_api_client, pink_attribute_value, permission_manage_products
):
    query = UPDATE_ATTRIBUTE_VALUE_QUERY
    value = pink_attribute_value
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    attr_value = "#BLUE"
    variables = {"name": value.name, "value": attr_value, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    assert not data["errors"]
    assert data["attributeValue"]["value"] == attr_value


def test_delete_attribute_value(
    staff_api_client, color_attribute, pink_attribute_value, permission_manage_products
):
    value = color_attribute.values.get(name="Red")
    query = """
    mutation updateChoice($id: ID!) {
        attributeValueDelete(id: $id) {
            attributeValue {
                name
                slug
            }
        }
    }
    """
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    variables = {"id": node_id}
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    with pytest.raises(value._meta.model.DoesNotExist):
        value.refresh_from_db()


@pytest.mark.parametrize(
    "raw_value, expected_type",
    [
        ("#0000", AttributeValueType.COLOR),
        ("#FF69B4", AttributeValueType.COLOR),
        ("rgb(255, 0, 0)", AttributeValueType.COLOR),
        ("hsl(0, 100%, 50%)", AttributeValueType.COLOR),
        ("hsla(120,  60%, 70%, 0.3)", AttributeValueType.COLOR),
        ("rgba(100%, 255, 0, 0)", AttributeValueType.COLOR),
        ("http://example.com", AttributeValueType.URL),
        ("https://example.com", AttributeValueType.URL),
        ("ftp://example.com", AttributeValueType.URL),
        ("example.com", AttributeValueType.STRING),
        ("Foo", AttributeValueType.STRING),
        ("linear-gradient(red, yellow)", AttributeValueType.GRADIENT),
        ("radial-gradient(#0000, yellow)", AttributeValueType.GRADIENT),
    ],
)
def test_resolve_attribute_value_type(raw_value, expected_type):
    assert resolve_attribute_value_type(raw_value) == expected_type


def test_resolve_attribute_list(color_attribute):
    value = color_attribute.values.first()
    attributes_json = {str(color_attribute.pk): [str(value.pk)]}
    res = resolve_attribute_list(attributes_json, Attribute.objects.all())
    assert len(res) == 1
    assert len(res[0].values) == 1
    assert res[0].attribute.name == color_attribute.name
    assert res[0].values[0].name == value.name

    # test passing invalid json should resolve to empty list
    attr_pk = str(Attribute.objects.order_by("pk").last().pk + 1)
    val_pk = str(AttributeValue.objects.order_by("pk").last().pk + 1)
    attributes_json = {attr_pk: [val_pk]}
    res = resolve_attribute_list(attributes_json, Attribute.objects.all())
    assert len(res) == 1
    assert res[0].attribute.pk == color_attribute.pk
    assert res[0].values == []


# FIXME: this field (value) is deprecated
def test_resolve_attribute_list_deprecated_single_value(color_attribute):
    value = color_attribute.values.first()

    # Test passing a value
    attributes_json = {str(color_attribute.pk): [str(value.pk)]}
    res = resolve_attribute_list(attributes_json, Attribute.objects.all())
    assert len(res) == 1
    assert len(res[0].values) == 1
    assert res[0].value.pk == value.pk

    # Test passing no values
    attributes_json = {str(color_attribute.pk): []}
    res = resolve_attribute_list(attributes_json, Attribute.objects.all())
    assert len(res) == 1
    assert res[0].values == []
    assert res[0].value is None


def test_resolve_assigned_attribute_without_values(api_client, product_type, product):
    # Remove all attributes and values from product
    product.attributes = {}
    product.save(update_fields=["attributes"])

    # Remove all attributes and values from variant
    variant = product.variants.get()
    variant.attributes = {}
    variant.save(update_fields=["attributes"])

    # Retrieve the product and variant's attributes
    products = get_graphql_content(
        api_client.post_graphql(
            """
        {
          products(first: 10) {
            edges {
              node {
                attributes {
                  attribute {
                    slug
                  }
                  values {
                    value
                  }
                }
                variants {
                  attributes {
                    attribute {
                      slug
                    }
                    values {
                      value
                    }
                  }
                }
              }
            }
          }
        }
    """
        )
    )["data"]["products"]["edges"]

    # Ensure we are only working on one product and variant, the ones we are testing
    assert len(products) == 1
    assert len(products[0]["node"]["variants"]) == 1

    # Retrieve the nodes data
    product = products[0]["node"]
    variant = product["variants"][0]

    # Ensure the product attributes values are all None
    assert len(product["attributes"]) == 1
    assert product["attributes"][0]["attribute"]["slug"] == "color"
    assert product["attributes"][0]["values"] == []

    # Ensure the variant attributes values are all None
    assert variant["attributes"][0]["attribute"]["slug"] == "size"
    assert variant["attributes"][0]["values"] == []


ASSIGN_ATTR_QUERY = """
    mutation assign($productTypeId: ID!, $operations: [AttributeAssignInput]!) {
      attributeAssign(productTypeId: $productTypeId, operations: $operations) {
        errors {
          field
          message
        }
        productType {
          id
          productAttributes {
            id
          }
          variantAttributes {
            id
          }
        }
      }
    }
"""


def test_assign_attributes_to_product_type(
    staff_api_client, permission_manage_products, attribute_list
):
    product_type = ProductType.objects.create(name="Default Type", has_variants=True)
    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    query = ASSIGN_ATTR_QUERY
    operations = []
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    product_attributes_ids = {attr.pk for attr in attribute_list[:2]}
    variant_attributes_ids = {attr.pk for attr in attribute_list[2:]}

    for attr_id in product_attributes_ids:
        operations.append(
            {"type": "PRODUCT", "id": graphene.Node.to_global_id("Attribute", attr_id)}
        )

    for attr_id in variant_attributes_ids:
        operations.append(
            {"type": "VARIANT", "id": graphene.Node.to_global_id("Attribute", attr_id)}
        )

    content = get_graphql_content(
        staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_products]
        )
    )["data"]["attributeAssign"]
    assert not content["errors"], "Should have succeeded"

    assert content["productType"]["id"] == product_type_global_id
    assert len(content["productType"]["productAttributes"]) == len(
        product_attributes_ids
    )
    assert len(content["productType"]["variantAttributes"]) == len(
        variant_attributes_ids
    )

    found_product_attrs_ids = {
        int(graphene.Node.from_global_id(attr["id"])[1])
        for attr in content["productType"]["productAttributes"]
    }
    found_variant_attrs_ids = {
        int(graphene.Node.from_global_id(attr["id"])[1])
        for attr in content["productType"]["variantAttributes"]
    }

    assert found_product_attrs_ids == product_attributes_ids
    assert found_variant_attrs_ids == variant_attributes_ids


def test_assign_variant_attribute_to_product_type_with_disabled_variants(
    staff_api_client,
    permission_manage_products,
    product_type_without_variant,
    color_attribute_without_values,
):
    """The assignAttribute mutation should raise an error when trying
    to add an attribute as a variant attribute when
    the product type doesn't support variants"""

    product_type = product_type_without_variant
    attribute = color_attribute_without_values
    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    query = ASSIGN_ATTR_QUERY
    operations = [
        {"type": "VARIANT", "id": graphene.Node.to_global_id("Attribute", attribute.pk)}
    ]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["attributeAssign"]
    assert content["errors"] == [
        {
            "field": "operations",
            "message": "Variants are disabled in this product type.",
        }
    ]


def test_assign_variant_attribute_having_unsupported_input_type(
    staff_api_client, permission_manage_products, product_type, size_attribute
):
    """The assignAttribute mutation should raise an error when trying
    to use an attribute as a variant attribute when
    the attribute's input type doesn't support variants"""

    attribute = size_attribute
    attribute.input_type = AttributeInputType.MULTISELECT
    attribute.save(update_fields=["input_type"])
    product_type.variant_attributes.clear()

    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    query = ASSIGN_ATTR_QUERY
    operations = [
        {"type": "VARIANT", "id": graphene.Node.to_global_id("Attribute", attribute.pk)}
    ]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["attributeAssign"]
    assert content["errors"] == [
        {
            "field": "operations",
            "message": (
                "Attributes having for input types ['multiselect'] cannot be assigned "
                "as variant attributes"
            ),
        }
    ]


@pytest.mark.parametrize(
    "product_type_attribute_type, gql_attribute_type",
    (
        (AttributeTypeEnum.PRODUCT, AttributeTypeEnum.VARIANT),
        (AttributeTypeEnum.VARIANT, AttributeTypeEnum.PRODUCT),
        (AttributeTypeEnum.PRODUCT, AttributeTypeEnum.PRODUCT),
        (AttributeTypeEnum.VARIANT, AttributeTypeEnum.VARIANT),
    ),
)
def test_assign_attribute_to_product_type_having_already_that_attribute(
    staff_api_client,
    permission_manage_products,
    color_attribute_without_values,
    product_type_attribute_type,
    gql_attribute_type,
):
    """The assignAttribute mutation should raise an error when trying
    to add an attribute already contained in the product type."""

    product_type = ProductType.objects.create(name="Type")
    attribute = color_attribute_without_values
    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    if product_type_attribute_type == AttributeTypeEnum.PRODUCT:
        product_type.product_attributes.add(attribute)
    elif product_type_attribute_type == AttributeTypeEnum.VARIANT:
        product_type.variant_attributes.add(attribute)
    else:
        raise ValueError(f"Unknown: {product_type}")

    query = ASSIGN_ATTR_QUERY
    operations = [
        {
            "type": gql_attribute_type.value,
            "id": graphene.Node.to_global_id("Attribute", attribute.pk),
        }
    ]
    variables = {"productTypeId": product_type_global_id, "operations": operations}

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["attributeAssign"]
    assert content["errors"] == [
        {
            "field": "operations",
            "message": "Color (color) have already been assigned to this product type.",
        }
    ]


UNASSIGN_ATTR_QUERY = """
    mutation unAssignAttribute(
      $productTypeId: ID!, $attributeIds: [ID]!
    ) {
      attributeUnassign(productTypeId: $productTypeId, attributeIds: $attributeIds) {
        errors {
          field
          message
        }
        productType {
          id
          variantAttributes {
            id
          }
          productAttributes {
            id
          }
        }
      }
    }
"""


def test_unassign_attributes_from_product_type(
    staff_api_client, permission_manage_products, attribute_list
):
    product_type = ProductType.objects.create(name="Type")
    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    variant_attribute, *product_attributes = attribute_list
    product_type.product_attributes.add(*product_attributes)
    product_type.variant_attributes.add(variant_attribute)

    remaining_attribute_global_id = graphene.Node.to_global_id(
        "Attribute", product_attributes[1].pk
    )

    query = UNASSIGN_ATTR_QUERY
    variables = {
        "productTypeId": product_type_global_id,
        "attributeIds": [
            graphene.Node.to_global_id("Attribute", product_attributes[0].pk)
        ],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_products]
        )
    )["data"]["attributeUnassign"]
    assert not content["errors"]

    assert content["productType"]["id"] == product_type_global_id
    assert len(content["productType"]["productAttributes"]) == 1
    assert len(content["productType"]["variantAttributes"]) == 1

    assert (
        content["productType"]["productAttributes"][0]["id"]
        == remaining_attribute_global_id
    )


def test_unassign_attributes_not_in_product_type(
    staff_api_client, permission_manage_products, color_attribute_without_values
):
    """The unAssignAttribute mutation should not raise any error when trying
    to remove an attribute that is not/no longer in the product type."""

    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_type = ProductType.objects.create(name="Type")
    product_type_global_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    query = UNASSIGN_ATTR_QUERY
    variables = {
        "productTypeId": product_type_global_id,
        "attributeIds": [
            graphene.Node.to_global_id("Attribute", color_attribute_without_values.pk)
        ],
    }

    content = get_graphql_content(staff_api_client.post_graphql(query, variables))[
        "data"
    ]["attributeUnassign"]
    assert not content["errors"]

    assert content["productType"]["id"] == product_type_global_id
    assert len(content["productType"]["productAttributes"]) == 0
    assert len(content["productType"]["variantAttributes"]) == 0


def test_retrieve_product_attributes_input_type(
    staff_api_client, product, permission_manage_products
):
    query = """
        {
          products(first: 10) {
            edges {
              node {
                attributes {
                  values {
                    type
                    inputType
                  }
                }
              }
            }
          }
        }
    """

    found_products = get_graphql_content(
        staff_api_client.post_graphql(query, permissions=[permission_manage_products])
    )["data"]["products"]["edges"]
    assert len(found_products) == 1

    for gql_attr in found_products[0]["node"]["attributes"]:
        assert len(gql_attr["values"]) == 1
        assert gql_attr["values"][0]["type"] == "STRING"
        assert gql_attr["values"][0]["inputType"] == "DROPDOWN"


@pytest.mark.parametrize(
    "attribute, expected_value",
    (
        ("filterable_in_storefront", True),
        ("filterable_in_dashboard", True),
        ("visible_in_storefront", True),
        ("available_in_grid", True),
        ("value_required", False),
        ("storefront_search_position", 0),
    ),
)
def test_retrieving_the_restricted_attributes_restricted(
    staff_api_client,
    color_attribute,
    permission_manage_products,
    attribute,
    expected_value,
):
    """Checks if the attributes are restricted and if their default value
    is the expected one."""

    attribute = to_camel_case(attribute)
    query = (
        """
        {
          attributes(first: 10) {
            edges {
              node {
                %s
              }
            }
          }
        }
    """
        % attribute
    )

    found_attributes = get_graphql_content(
        staff_api_client.post_graphql(query, permissions=[permission_manage_products])
    )["data"]["attributes"]["edges"]

    assert len(found_attributes) == 1
    assert found_attributes[0]["node"][attribute] == expected_value


ATTRIBUTES_RESORT_QUERY = """
    mutation ProductTypeReorderAttributes(
      $productTypeId: ID!
      $moves: [ReorderInput]!
      $type: AttributeTypeEnum!
    ) {
      productTypeReorderAttributes(
        productTypeId: $productTypeId
        moves: $moves
        type: $type
      ) {
        productType {
          id
          variantAttributes {
            id
            slug
          }
          productAttributes {
            id
          }
        }

        errors {
          field
          message
        }
      }
    }
"""


def test_sort_attributes_within_product_type_invalid_product_type(
    staff_api_client, permission_manage_products
):
    """Try to reorder an invalid product type (invalid ID)."""

    product_type_id = graphene.Node.to_global_id("ProductType", -1)
    attribute_id = graphene.Node.to_global_id("Attribute", -1)

    variables = {
        "type": "VARIANT",
        "productTypeId": product_type_id,
        "moves": [{"id": attribute_id, "sortOrder": 1}],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(
            ATTRIBUTES_RESORT_QUERY, variables, permissions=[permission_manage_products]
        )
    )["data"]["productTypeReorderAttributes"]

    assert content["errors"] == [
        {
            "field": "productTypeId",
            "message": f"Couldn't resolve to a product type: {product_type_id}",
        }
    ]


def test_sort_attributes_within_product_type_invalid_id(
    staff_api_client, permission_manage_products, color_attribute
):
    """Try to reorder an attribute not associated to the given product type."""

    product_type = ProductType.objects.create(name="Dummy Type")
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)

    variables = {
        "type": "VARIANT",
        "productTypeId": product_type_id,
        "moves": [{"id": attribute_id, "sortOrder": 1}],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(
            ATTRIBUTES_RESORT_QUERY, variables, permissions=[permission_manage_products]
        )
    )["data"]["productTypeReorderAttributes"]

    assert content["errors"] == [
        {
            "field": "moves",
            "message": f"Couldn't resolve to an attribute: {attribute_id}",
        }
    ]


@pytest.mark.parametrize(
    "attribute_type, relation_field, backref_field",
    (
        ("VARIANT", "variant_attributes", "attributevariant"),
        ("PRODUCT", "product_attributes", "attributeproduct"),
    ),
)
def test_sort_attributes_within_product_type(
    staff_api_client,
    attribute_list,
    permission_manage_products,
    attribute_type,
    relation_field,
    backref_field,
):
    attributes = attribute_list
    assert len(attributes) == 3

    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_type = ProductType.objects.create(name="Dummy Type")
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)
    m2m_attributes = getattr(product_type, relation_field)
    m2m_attributes.set(attributes)

    sort_method = getattr(m2m_attributes, f"{relation_field}_sorted")
    attributes = list(sort_method())

    assert len(attributes) == 3

    variables = {
        "type": attribute_type,
        "productTypeId": product_type_id,
        "moves": [
            {
                "id": graphene.Node.to_global_id("Attribute", attributes[0].pk),
                "sortOrder": +1,
            },
            {
                "id": graphene.Node.to_global_id("Attribute", attributes[2].pk),
                "sortOrder": -1,
            },
        ],
    }

    expected_order = [attributes[1].pk, attributes[2].pk, attributes[0].pk]

    content = get_graphql_content(
        staff_api_client.post_graphql(ATTRIBUTES_RESORT_QUERY, variables)
    )["data"]["productTypeReorderAttributes"]
    assert not content["errors"]

    assert (
        content["productType"]["id"] == product_type_id
    ), "Did not return the correct product type"

    gql_attributes = content["productType"][snake_to_camel_case(relation_field)]
    assert len(gql_attributes) == len(expected_order)

    for attr, expected_pk in zip(gql_attributes, expected_order):
        gql_type, gql_attr_id = graphene.Node.from_global_id(attr["id"])
        assert gql_type == "Attribute"
        assert int(gql_attr_id) == expected_pk


ATTRIBUTE_VALUES_RESORT_QUERY = """
    mutation attributeReorderValues($attributeId: ID!, $moves: [ReorderInput]!) {
      attributeReorderValues(attributeId: $attributeId, moves: $moves) {
        attribute {
          id
          values {
            id
          }
        }

        errors {
          field
          message
        }
      }
    }
"""


def test_sort_values_within_attribute_invalid_product_type(
    staff_api_client, permission_manage_products
):
    """Try to reorder an invalid attribute (invalid ID)."""

    attribute_id = graphene.Node.to_global_id("Attribute", -1)
    value_id = graphene.Node.to_global_id("AttributeValue", -1)

    variables = {
        "attributeId": attribute_id,
        "moves": [{"id": value_id, "sortOrder": 1}],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(
            ATTRIBUTE_VALUES_RESORT_QUERY,
            variables,
            permissions=[permission_manage_products],
        )
    )["data"]["attributeReorderValues"]

    assert content["errors"] == [
        {
            "field": "attributeId",
            "message": f"Couldn't resolve to an attribute: {attribute_id}",
        }
    ]


def test_sort_values_within_attribute_invalid_id(
    staff_api_client, permission_manage_products, color_attribute
):
    """Try to reorder a value not associated to the given attribute."""

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    value_id = graphene.Node.to_global_id("AttributeValue", -1)

    variables = {
        "type": "VARIANT",
        "attributeId": attribute_id,
        "moves": [{"id": value_id, "sortOrder": 1}],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(
            ATTRIBUTE_VALUES_RESORT_QUERY,
            variables,
            permissions=[permission_manage_products],
        )
    )["data"]["attributeReorderValues"]

    assert content["errors"] == [
        {
            "field": "moves",
            "message": f"Couldn't resolve to an attribute value: {value_id}",
        }
    ]


def test_sort_values_within_attribute(
    staff_api_client, color_attribute, permission_manage_products
):
    attribute = color_attribute
    AttributeValue.objects.create(attribute=attribute, name="Green", slug="green")
    values = list(attribute.values.all())
    assert len(values) == 3

    staff_api_client.user.user_permissions.add(permission_manage_products)

    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    m2m_values = attribute.values
    m2m_values.set(values)

    assert values == sorted(
        values, key=lambda o: o.sort_order if o.sort_order is not None else o.pk
    ), "The values are not properly ordered"

    variables = {
        "attributeId": attribute_id,
        "moves": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", values[0].pk),
                "sortOrder": +1,
            },
            {
                "id": graphene.Node.to_global_id("AttributeValue", values[2].pk),
                "sortOrder": -1,
            },
        ],
    }

    expected_order = [values[1].pk, values[2].pk, values[0].pk]

    content = get_graphql_content(
        staff_api_client.post_graphql(ATTRIBUTE_VALUES_RESORT_QUERY, variables)
    )["data"]["attributeReorderValues"]
    assert not content["errors"]

    assert content["attribute"]["id"] == attribute_id

    gql_values = content["attribute"]["values"]
    assert len(gql_values) == len(expected_order)

    actual_order = []

    for attr, expected_pk in zip(gql_values, expected_order):
        gql_type, gql_attr_id = graphene.Node.from_global_id(attr["id"])
        assert gql_type == "AttributeValue"
        actual_order.append(int(gql_attr_id))

    assert actual_order == expected_order


ATTRIBUTES_FILTER_QUERY = """
    query($filters: AttributeFilterInput!) {
      attributes(first: 10, filter: $filters) {
        edges {
          node {
            name
            slug
          }
        }
      }
    }
"""


def test_search_attributes(api_client, color_attribute, size_attribute):
    variables = {"filters": {"search": "color"}}

    attributes = get_graphql_content(
        api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    assert len(attributes) == 1
    assert attributes[0]["node"]["slug"] == "color"


def test_filter_attributes_if_filterable_in_dashboard(
    api_client, color_attribute, size_attribute
):
    color_attribute.filterable_in_dashboard = False
    color_attribute.save(update_fields=["filterable_in_dashboard"])

    variables = {"filters": {"filterableInDashboard": True}}

    attributes = get_graphql_content(
        api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    assert len(attributes) == 1
    assert attributes[0]["node"]["slug"] == "size"


def test_filter_attributes_if_available_in_grid(
    api_client, color_attribute, size_attribute
):
    color_attribute.available_in_grid = False
    color_attribute.save(update_fields=["available_in_grid"])

    variables = {"filters": {"availableInGrid": True}}

    attributes = get_graphql_content(
        api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    assert len(attributes) == 1
    assert attributes[0]["node"]["slug"] == "size"


def test_filter_attributes_by_global_id_list(api_client, attribute_list):
    global_ids = [
        graphene.Node.to_global_id("Attribute", attribute.pk)
        for attribute in attribute_list[:2]
    ]
    variables = {"filters": {"ids": global_ids}}

    expected_slugs = sorted([attribute_list[0].slug, attribute_list[1].slug])

    attributes = get_graphql_content(
        api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    assert len(attributes) == 2
    received_slugs = sorted(
        [attributes[0]["node"]["slug"], attributes[1]["node"]["slug"]]
    )

    assert received_slugs == expected_slugs


ATTRIBUTES_SORT_QUERY = """
    query($sortBy: AttributeSortingInput) {
      attributes(first: 10, sortBy: $sortBy) {
        edges {
          node {
            slug
          }
        }
      }
    }
"""


def test_sort_attributes_by_slug(api_client):
    Attribute.objects.bulk_create(
        [
            Attribute(name="MyAttribute", slug="b"),
            Attribute(name="MyAttribute", slug="a"),
        ]
    )

    variables = {"sortBy": {"field": "SLUG", "direction": "ASC"}}

    attributes = get_graphql_content(
        api_client.post_graphql(ATTRIBUTES_SORT_QUERY, variables)
    )["data"]["attributes"]["edges"]

    assert len(attributes) == 2
    assert attributes[0]["node"]["slug"] == "a"
    assert attributes[1]["node"]["slug"] == "b"


@pytest.mark.parametrize(
    "sort_field, m2m_model",
    (
        ("DASHBOARD_VARIANT_POSITION", AttributeVariant),
        ("DASHBOARD_PRODUCT_POSITION", AttributeProduct),
    ),
)
def test_sort_attributes_by_position_in_product_type(
    api_client,
    color_attribute,
    size_attribute,
    sort_field: str,
    m2m_model: Union[AttributeVariant, AttributeProduct],
):
    """Sorts attributes for dashboard custom ordering inside a given product type."""

    product_type = ProductType.objects.create(name="My Product Type")
    m2m_model.objects.create(
        product_type=product_type, attribute=color_attribute, sort_order=0
    )
    m2m_model.objects.create(
        product_type=product_type, attribute=size_attribute, sort_order=1
    )

    variables = {"sortBy": {"field": sort_field, "direction": "DESC"}}

    attributes = get_graphql_content(
        api_client.post_graphql(ATTRIBUTES_SORT_QUERY, variables)
    )["data"]["attributes"]["edges"]

    assert len(attributes) == 2
    assert attributes[0]["node"]["slug"] == "size"
    assert attributes[1]["node"]["slug"] == "color"


def test_sort_attributes_by_default_sorting(api_client):
    """Don't provide any sorting, this should sort by name by default."""
    Attribute.objects.bulk_create(
        [Attribute(name="A", slug="b"), Attribute(name="B", slug="a")]
    )

    attributes = get_graphql_content(
        api_client.post_graphql(ATTRIBUTES_SORT_QUERY, {})
    )["data"]["attributes"]["edges"]

    assert len(attributes) == 2
    assert attributes[0]["node"]["slug"] == "b"
    assert attributes[1]["node"]["slug"] == "a"


@pytest.mark.parametrize("is_variant", (True, False))
def test_attributes_of_products_are_sorted(
    staff_api_client, product, color_attribute, is_variant
):
    """Ensures the attributes of products and variants are sorted."""

    variant = product.variants.first()

    if is_variant:
        query = """
            query($id: ID!) {
              productVariant(id: $id) {
                attributes {
                  attribute {
                    id
                  }
                }
              }
            }
        """
    else:
        query = """
            query($id: ID!) {
              product(id: $id) {
                attributes {
                  attribute {
                    id
                  }
                }
              }
            }
        """

    # Create a dummy attribute with a higher ID
    # This will allow us to make sure it is always the last attribute
    # when sorted by ID. Thus, we are sure the query is actually passing the test.
    other_attribute = Attribute.objects.create(name="Other", slug="other")

    # Add the attribute to the product type
    if is_variant:
        product.product_type.variant_attributes.set([color_attribute, other_attribute])
    else:
        product.product_type.product_attributes.set([color_attribute, other_attribute])

    # Retrieve the M2M object for the attribute vs the product type
    if is_variant:
        m2m_rel_other_attr = other_attribute.attributevariant.last()
    else:
        m2m_rel_other_attr = other_attribute.attributeproduct.last()

    # Push the last attribute to the top and let the others to None
    m2m_rel_other_attr.sort_order = 0
    m2m_rel_other_attr.save(update_fields=["sort_order"])

    # Assign attributes to the product
    node = variant if is_variant else product
    node.attributes = {
        str(color_attribute.pk): [str(color_attribute.values.first().pk)]
    }
    node.save(update_fields=["attributes"])

    # Sort the database attributes by their sort order and ID (when None)
    expected_order = [other_attribute.pk, color_attribute.pk]

    # Make the node ID
    if is_variant:
        node_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    else:
        node_id = graphene.Node.to_global_id("Product", product.pk)

    # Retrieve the attributes
    data = get_graphql_content(staff_api_client.post_graphql(query, {"id": node_id}))[
        "data"
    ]
    attributes = data["productVariant" if is_variant else "product"]["attributes"]
    actual_order = [
        int(graphene.Node.from_global_id(attr["attribute"]["id"])[1])
        for attr in attributes
    ]

    # Compare the received data against our expectations
    assert actual_order == expected_order
