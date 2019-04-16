import graphene
import pytest
from django.db.models import Q
from django.template.defaultfilters import slugify

from saleor.graphql.product.enums import AttributeTypeEnum, AttributeValueType
from saleor.graphql.product.types.attributes import (
    resolve_attribute_value_type)
from saleor.graphql.product.utils import attributes_to_hstore
from saleor.product.models import Attribute, AttributeValue, Category
from tests.api.utils import get_graphql_content


def test_attributes_to_hstore(product, color_attribute):
    color_value = color_attribute.values.first()

    # test transforming slugs of existing attributes to IDs
    input_data = [{
        'slug': color_attribute.slug, 'value': color_value.slug}]
    attrs_qs = product.product_type.product_attributes.all()
    ids = attributes_to_hstore(input_data, attrs_qs)
    assert str(color_attribute.pk) in ids
    assert ids[str(color_attribute.pk)] == str(color_value.pk)

    # test creating a new attribute value
    input_data = [{
        'slug': color_attribute.slug, 'value': 'Space Grey'}]
    ids = attributes_to_hstore(input_data, attrs_qs)
    new_value = AttributeValue.objects.get(slug='space-grey')
    assert str(color_attribute.pk) in ids
    assert ids[str(color_attribute.pk)] == str(new_value.pk)

    # test passing an attribute that doesn't belong to this product raises
    # an error
    input_data = [{'slug': 'not-an-attribute', 'value': 'not-a-value'}]
    with pytest.raises(ValueError):
        attributes_to_hstore(input_data, attrs_qs)


def test_attributes_query(user_api_client, product):
    attributes = Attribute.objects.prefetch_related('values')
    query = """
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
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    attributes_data = content['data']['attributes']['edges']
    assert len(attributes_data) == attributes.count()


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
                    values {
                        id
                        name
                        slug
                    }
                }
            }
        }
    }
    """ % {'category_id': graphene.Node.to_global_id('Category', category.id)}
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    attributes_data = content['data']['attributes']['edges']
    assert len(attributes_data) == Attribute.objects.count()


def test_attributes_in_collection_query(user_api_client, sale):
    product_types = set(
        sale.products.all().values_list('product_type_id', flat=True))
    expected_attrs = Attribute.objects.filter(
        Q(product_type__in=product_types)
        | Q(product_variant_type__in=product_types))

    query = """
    query {
        attributes(inCollection: "%(collection_id)s", first: 20) {
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
    """ % {'collection_id': graphene.Node.to_global_id('Collection', sale.id)}
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    attributes_data = content['data']['attributes']['edges']
    assert len(attributes_data) == len(expected_attrs)


CREATE_ATTRIBUTES_QUERY = """
    mutation createAttribute(
        $name: String!, $values: [AttributeValueCreateInput],
        $id: ID!, $type: AttributeTypeEnum!) {
    attributeCreate(
            id: $id, type: $type, input: {name: $name, values: $values}) {
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
        }
        productType {
            id
            name
        }
    }
}
"""


def test_create_attribute_and_attribute_values(
        staff_api_client, permission_manage_products, product_type):
    query = CREATE_ATTRIBUTES_QUERY
    node_id = graphene.Node.to_global_id('ProductType', product_type.id)

    attribute_name = 'Example name'
    name = 'Value name'
    variables = {
        'name': attribute_name, 'id': node_id,
        'type': AttributeTypeEnum.PRODUCT.name,
        'values': [{'name': name, 'value': '#1231'}]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    assert not content['data']['attributeCreate']['errors']
    data = content['data']['attributeCreate']
    assert data['attribute']['name'] == attribute_name
    assert data['attribute']['slug'] == slugify(attribute_name)

    assert len(data['attribute']['values']) == 1
    assert data['attribute']['values'][0]['name'] == name
    assert data['attribute']['values'][0]['slug'] == slugify(name)
    attribute = Attribute.objects.get(name=attribute_name)
    assert attribute in product_type.product_attributes.all()
    assert data['productType']['name'] == product_type.name


@pytest.mark.parametrize(
    'name_1, name_2, error_msg', (
        (
            'Red color', 'Red color',
            'Provided values are not unique.'),
        (
            'Red color', 'red color',
            'Provided values are not unique.')))
def test_create_attribute_and_attribute_values_errors(
        staff_api_client, name_1, name_2, error_msg,
        permission_manage_products, product_type):
    query = CREATE_ATTRIBUTES_QUERY
    node_id = graphene.Node.to_global_id('ProductType', product_type.id)
    variables = {
        'name': 'Example name', 'id': node_id,
        'type': AttributeTypeEnum.PRODUCT.name,
        'values': [
            {'name': name_1, 'value': '#1231'},
            {'name': name_2, 'value': '#121'}]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    errors = content['data']['attributeCreate']['errors']
    assert errors
    assert errors[0]['field'] == 'values'
    assert errors[0]['message'] == error_msg


def test_create_variant_attribute(
        staff_api_client, permission_manage_products, product_type):
    product_type.has_variants = True
    product_type.save()

    query = CREATE_ATTRIBUTES_QUERY
    node_id = graphene.Node.to_global_id('ProductType', product_type.id)
    attribute_name = 'Example name'
    variables = {
        'name': attribute_name, 'id': node_id,
        'type': AttributeTypeEnum.VARIANT.name, 'values': []}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    assert not content['data']['attributeCreate']['errors']
    attribute = Attribute.objects.get(name=attribute_name)
    assert attribute in product_type.variant_attributes.all()


def test_create_attribute_incorrect_product_type_id(
        staff_api_client, permission_manage_products, product_type):
    query = CREATE_ATTRIBUTES_QUERY
    variables = {
        'name': 'Example name', 'id': 'incorrect-id',
        'type': AttributeTypeEnum.PRODUCT.name, 'values': []}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    errors = content['data']['attributeCreate']['errors']
    assert errors[0]['field'] == 'id'


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
        }
        productType {
            id
            name
        }
    }
}
"""


def test_update_attribute_name(
        staff_api_client, color_attribute, product_type,
        permission_manage_products):
    query = UPDATE_ATTRIBUTE_QUERY
    attribute = color_attribute
    name = 'Wings name'
    node_id = graphene.Node.to_global_id('Attribute', attribute.id)
    variables = {
        'name': name, 'id': node_id, 'addValues': [], 'removeValues': []}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content['data']['attributeUpdate']
    assert data['attribute']['name'] == name == attribute.name
    assert data['productType']['name'] == attribute.product_type.name


def test_update_attribute_remove_and_add_values(
        staff_api_client, color_attribute, permission_manage_products):
    query = UPDATE_ATTRIBUTE_QUERY
    attribute = color_attribute
    name = 'Wings name'
    attribute_value_name = 'Red Color'
    node_id = graphene.Node.to_global_id('Attribute', attribute.id)
    attribute_value_id = attribute.values.first().id
    value_id = graphene.Node.to_global_id(
        'AttributeValue', attribute_value_id)
    variables = {
        'name': name, 'id': node_id,
        'addValues': [{'name': attribute_value_name, 'value': '#1231'}],
        'removeValues': [value_id]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content['data']['attributeUpdate']
    assert not data['errors']
    assert data['attribute']['name'] == name == attribute.name
    assert not attribute.values.filter(pk=attribute_value_id).exists()
    assert attribute.values.filter(name=attribute_value_name).exists()


def test_update_empty_attribute_and_add_values(
        staff_api_client, color_attribute_without_values,
        permission_manage_products):
    query = UPDATE_ATTRIBUTE_QUERY
    attribute = color_attribute_without_values
    name = 'Wings name'
    attribute_value_name = 'Yellow Color'
    node_id = graphene.Node.to_global_id('Attribute', attribute.id)
    variables = {
        'name': name, 'id': node_id,
        'addValues': [{'name': attribute_value_name, 'value': '#1231'}],
        'removeValues': []}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    get_graphql_content(response)
    attribute.refresh_from_db()
    assert attribute.values.count() == 1
    assert attribute.values.filter(name=attribute_value_name).exists()


@pytest.mark.parametrize(
    'name_1, name_2, error_msg', (
        (
            'Red color', 'Red color',
            'Provided values are not unique.'),
        (
            'Red color', 'red color',
            'Provided values are not unique.')))
def test_update_attribute_and_add_attribute_values_errors(
        staff_api_client, name_1, name_2, error_msg, color_attribute,
        permission_manage_products):
    query = UPDATE_ATTRIBUTE_QUERY
    attribute = color_attribute
    node_id = graphene.Node.to_global_id('Attribute', attribute.id)
    variables = {
        'name': 'Example name', 'id': node_id, 'removeValues': [],
        'addValues': [
            {'name': name_1, 'value': '#1'}, {'name': name_2, 'value': '#2'}]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    errors = content['data']['attributeUpdate']['errors']
    assert errors
    assert errors[0]['field'] == 'addValues'
    assert errors[0]['message'] == error_msg


def test_update_attribute_and_remove_others_attribute_value(
        staff_api_client, color_attribute, size_attribute,
        permission_manage_products):
    query = UPDATE_ATTRIBUTE_QUERY
    attribute = color_attribute
    node_id = graphene.Node.to_global_id('Attribute', attribute.id)
    size_attribute = size_attribute.values.first()
    attr_id = graphene.Node.to_global_id(
        'AttributeValue', size_attribute.pk)
    variables = {
        'name': 'Example name', 'id': node_id, 'slug': 'example-slug',
        'addValues': [], 'removeValues': [attr_id]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    errors = content['data']['attributeUpdate']['errors']
    assert errors
    assert errors[0]['field'] == 'removeValues'
    err_msg = (
        'Value %s does not belong to this attribute.' % str(size_attribute))
    assert errors[0]['message'] == err_msg


def test_delete_attribute(
        staff_api_client, color_attribute, permission_manage_products,
        product_type):
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
            productType {
                name
            }
        }
    }
    """
    node_id = graphene.Node.to_global_id('Attribute', attribute.id)
    variables = {'id': node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['attributeDelete']
    assert data['productType']['name'] == attribute.product_type.name
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
        staff_api_client, color_attribute, permission_manage_products):
    attribute = color_attribute
    query = CREATE_ATTRIBUTE_VALUE_QUERY
    attribute_id = graphene.Node.to_global_id('Attribute', attribute.id)
    name = 'test name'
    value = 'test-string'
    variables = {'name': name, 'value': value, 'attributeId': attribute_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['attributeValueCreate']
    assert not data['errors']

    attr_data = data['attributeValue']
    assert attr_data['name'] == name
    assert attr_data['slug'] == slugify(name)
    assert attr_data['value'] == value
    assert attr_data['type'] == 'STRING'
    assert name in [value['name'] for value in data['attribute']['values']]


def test_create_attribute_value_not_unique_name(
        staff_api_client, color_attribute, permission_manage_products):
    attribute = color_attribute
    query = CREATE_ATTRIBUTE_VALUE_QUERY
    attribute_id = graphene.Node.to_global_id('Attribute', attribute.id)
    value_name = attribute.values.first().name
    variables = {
        'name': value_name, 'value': 'test-string',
        'attributeId': attribute_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['attributeValueCreate']
    assert data['errors']
    assert data['errors'][0]['message']
    assert not data['errors'][0]['field']


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
        staff_api_client, pink_attribute_value, permission_manage_products):
    query = UPDATE_ATTRIBUTE_VALUE_QUERY
    value = pink_attribute_value
    node_id = graphene.Node.to_global_id('AttributeValue', value.id)
    name = 'Crimson name'
    variables = {'name': name, 'value': '#RED', 'id': node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['attributeValueUpdate']
    value.refresh_from_db()
    assert data['attributeValue']['name'] == name == value.name
    assert data['attributeValue']['slug'] == slugify(name)
    assert name in [value['name'] for value in data['attribute']['values']]


def test_update_attribute_value_name_not_unique(
        staff_api_client, pink_attribute_value, permission_manage_products):
    query = UPDATE_ATTRIBUTE_VALUE_QUERY
    value = pink_attribute_value.attribute.values.create(
        name='Example Name', slug='example-name', value='#RED')
    node_id = graphene.Node.to_global_id('AttributeValue', value.id)
    variables = {
        'name': pink_attribute_value.name, 'value': '#RED', 'id': node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['attributeValueUpdate']
    assert data['errors']
    assert data['errors'][0]['message']
    assert not data['errors'][0]['field']


def test_update_same_attribute_value(
        staff_api_client, pink_attribute_value, permission_manage_products):
    query = UPDATE_ATTRIBUTE_VALUE_QUERY
    value = pink_attribute_value
    node_id = graphene.Node.to_global_id('AttributeValue', value.id)
    attr_value = '#BLUE'
    variables = {'name': value.name, 'value': attr_value, 'id': node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['attributeValueUpdate']
    assert not data['errors']
    assert data['attributeValue']['value'] == attr_value


def test_delete_attribute_value(
        staff_api_client, color_attribute, pink_attribute_value,
        permission_manage_products):
    value = color_attribute.values.get(name='Red')
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
    node_id = graphene.Node.to_global_id('AttributeValue', value.id)
    variables = {'id': node_id}
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    with pytest.raises(value._meta.model.DoesNotExist):
        value.refresh_from_db()


@pytest.mark.parametrize('raw_value, expected_type', [
    ('#0000', AttributeValueType.COLOR),
    ('#FF69B4', AttributeValueType.COLOR),
    ('rgb(255, 0, 0)', AttributeValueType.COLOR),
    ('hsl(0, 100%, 50%)', AttributeValueType.COLOR),
    ('hsla(120,  60%, 70%, 0.3)', AttributeValueType.COLOR),
    ('rgba(100%, 255, 0, 0)', AttributeValueType.COLOR),
    ('http://example.com', AttributeValueType.URL),
    ('https://example.com', AttributeValueType.URL),
    ('ftp://example.com', AttributeValueType.URL),
    ('example.com', AttributeValueType.STRING),
    ('Foo', AttributeValueType.STRING),
    ('linear-gradient(red, yellow)', AttributeValueType.GRADIENT),
    ('radial-gradient(#0000, yellow)', AttributeValueType.GRADIENT),
])
def test_resolve_attribute_value_type(raw_value, expected_type):
    assert resolve_attribute_value_type(raw_value) == expected_type
