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
