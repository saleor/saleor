import json

import graphene
import pytest
from django.shortcuts import reverse
from tests.utils import get_graphql_content
from .utils import assert_read_only_mode


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
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)
