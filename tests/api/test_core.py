from unittest.mock import Mock

import graphene
from saleor.graphql.core.utils import clean_seo_fields, snake_to_camel_case
from saleor.graphql.product import types as product_types
from saleor.graphql.utils import get_database_id
from tests.api.utils import get_graphql_content


def test_clean_seo_fields():
    title = 'lady title'
    description = 'fantasy description'
    data = {'seo':
                {'title': title,
                 'description': description}}
    clean_seo_fields(data)
    assert data['seo_title'] == title
    assert data['seo_description'] == description


def test_user_error_field_name_for_related_object(admin_api_client):
    query = """
    mutation {
        categoryCreate(input: {name: "Test", parent: "123456"}) {
            errors {
                field
                message
            }
            category {
                id
            }
        }
    }
    """
    response = admin_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content['data']['categoryCreate']['category']
    assert data is None
    error = content['data']['categoryCreate']['errors'][0]
    assert error['field'] == 'parent'


def test_get_database_id(product):
    info = Mock(
        schema=Mock(
            get_type=Mock(
                return_value=Mock(graphene_type=product_types.Product))))
    node_id = graphene.Node.to_global_id('Product', product.pk)
    pk = get_database_id(info, node_id, product_types.Product)
    assert int(pk) == product.pk


def test_snake_to_camel_case():
    assert snake_to_camel_case('test_camel_case') == 'testCamelCase'
    assert snake_to_camel_case('testCamel_case') == 'testCamelCase'
    assert snake_to_camel_case(123) == 123


def test_mutation_returns_error_field_in_camel_case(admin_api_client, variant):
    # costPrice is snake case variable (cost_price) in the backend
    query = """
    mutation testCamel($id: ID!, $cost: Decimal) {
        productVariantUpdate(id: $id,
        input: {costPrice: $cost, trackInventory: false}) {
            errors {
                field
                message
            }
            productVariant {
                id
            }
        }
    }
    """
    variables = {
        'id': graphene.Node.to_global_id('ProductVariant', variant.id),
        'cost': 12.1234}
    response = admin_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content['data']['productVariantUpdate']['errors'][0]
    assert error['field'] == 'costPrice'
