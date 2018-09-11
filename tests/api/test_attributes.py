import json

import graphene
import pytest
from django.shortcuts import reverse
from tests.utils import get_graphql_content
from saleor.product.models import (
    Category, ProductAttribute, AttributeChoiceValue)
from saleor.graphql.product.utils import attributes_to_hstore


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
    new_value = AttributeChoiceValue.objects.get(slug='space-grey')
    assert str(color_attribute.pk) in ids
    assert ids[str(color_attribute.pk)] == str(new_value.pk)

    # test passing an attribute that doesn't belong to this product raises
    # an error
    input_data = [{'slug': 'not-an-attribute', 'value': 'not-a-value'}]
    with pytest.raises(ValueError):
        attributes_to_hstore(input_data, attrs_qs)


def test_attributes_query(user_api_client, product):
    attributes = ProductAttribute.objects.prefetch_related('values')
    query = '''
    query {
        attributes {
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
    '''
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    attributes_data = content['data']['attributes']['edges']
    assert len(attributes_data) == attributes.count()


def test_attributes_in_category_query(user_api_client, product):
    category = Category.objects.first()
    query = '''
    query {
        attributes(inCategory: "%(category_id)s") {
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
    ''' % {'category_id': graphene.Node.to_global_id('Category', category.id)}
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    attributes_data = content['data']['attributes']['edges']
    assert len(attributes_data) == ProductAttribute.objects.count()


def test_create_product_attribute(admin_api_client):
    query = """
    mutation createAttribute($name: String!, $slug: String!) {
        productAttributeCreate(input: {name: $name, slug: $slug}) {
            productAttribute {
                name
                slug
                values {
                    name
                    slug
                }
            }
        }
    }
    """
    name = 'test name'
    slug = 'test-slug'
    variables = json.dumps({'name': name, 'slug': slug})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['productAttributeCreate']['productAttribute']
    assert data['name'] == name
    assert data['slug'] == slug
    assert not data['values']


def test_update_product_attribute(admin_api_client, color_attribute):
    attribute = color_attribute
    query = """
    mutation updateAttribute($id: ID!, $name: String!, $slug: String!) {
        productAttributeUpdate(id: $id, input: {name: $name, slug: $slug}) {
            productAttribute {
                name
            }
        }
    }
    """
    name = 'Wings name'
    slug = attribute.slug
    id = graphene.Node.to_global_id('ProductAttribute', attribute.id)
    variables = json.dumps({'name': name, 'id': id, 'slug': slug})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    assert 'errors' not in content
    data = content['data']['productAttributeUpdate']['productAttribute']
    assert data['name'] == name == attribute.name


def test_delete_product_attribute(admin_api_client, color_attribute):
    attribute = color_attribute
    query = """
    mutation deleteAttribute($id: ID!) {
        productAttributeDelete(id: $id) {
            productAttribute {
                id
            }
        }
    }
    """
    id = graphene.Node.to_global_id('ProductAttribute', attribute.id)
    variables = json.dumps({'id': id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    with pytest.raises(attribute._meta.model.DoesNotExist):
        attribute.refresh_from_db()


def test_create_attribute_choice_value(admin_api_client, color_attribute):
    attribute = color_attribute
    query = """
    mutation createChoice($attribute: ID!, $name: String!, $slug: String!) {
        attributeChoiceValueCreate(
        input: {attribute: $attribute, name: $name, slug: $slug}) {
            attributeChoiceValue {
                name
                slug
            }
        }
    }
    """
    attribute_id = graphene.Node.to_global_id('ProductAttribute', attribute.id)
    name = 'test name'
    slug = 'test-slug'
    variables = json.dumps(
        {'name': name, 'slug': slug, 'attribute': attribute_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content[
        'data']['attributeChoiceValueCreate']['attributeChoiceValue']
    assert data['name'] == name
    assert data['slug'] == slug


def test_update_attribute_choice_value(admin_api_client, pink_choice_value):
    value = pink_choice_value
    query = """
    mutation updateChoice($id: ID!, $name: String!, $slug: String!) {
        attributeChoiceValueUpdate(
        id: $id, input: {name: $name, slug: $slug}) {
            attributeChoiceValue {
                name
                slug
            }
        }
    }
    """
    id = graphene.Node.to_global_id('ProductAttributeValue', value.id)
    name = 'Crimson'
    slug = value.slug
    variables = json.dumps(
        {'name': name, 'slug': slug, 'id': id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    value.refresh_from_db()
    data = content[
        'data']['attributeChoiceValueUpdate']['attributeChoiceValue']
    assert data['name'] == name == value.name


def test_delete_attribute_choice_value(admin_api_client, color_attribute, pink_choice_value):
    value = pink_choice_value
    value = color_attribute.values.get(name='Red')
    query = """
    mutation updateChoice($id: ID!) {
        attributeChoiceValueDelete(id: $id) {
            attributeChoiceValue {
                name
                slug
            }
        }
    }
    """
    id = graphene.Node.to_global_id('ProductAttributeValue', value.id)
    variables = json.dumps({'id': id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    with pytest.raises(value._meta.model.DoesNotExist):
        value.refresh_from_db()
