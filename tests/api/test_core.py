from unittest.mock import Mock

import graphene
from django.utils import timezone
from tests.api.utils import (
    _get_graphql_content_from_response, get_graphql_content)

from saleor.graphql.core.types import ReportingPeriod
from saleor.graphql.core.utils import clean_seo_fields, snake_to_camel_case
from saleor.graphql.product import types as product_types
from saleor.graphql.utils import get_database_id, reporting_period_to_date
from saleor.product.models import Product


def test_clean_seo_fields():
    title = 'lady title'
    description = 'fantasy description'
    data = {'seo':
                {'title': title,
                 'description': description}}
    clean_seo_fields(data)
    assert data['seo_title'] == title
    assert data['seo_description'] == description


def test_user_error_field_name_for_related_object(
        staff_api_client, permission_manage_products):
    query = """
    mutation {
        categoryCreate(input: {name: "Test"}, parent: "123456") {
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
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_products])
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


def test_mutation_returns_error_field_in_camel_case(
        staff_api_client, variant, permission_manage_products):
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
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    error = content['data']['productVariantUpdate']['errors'][0]
    assert error['field'] == 'costPrice'


def test_reporting_period_to_date():
    now = timezone.now()
    start_date = reporting_period_to_date(ReportingPeriod.TODAY)
    assert start_date.day == now.day
    assert start_date.hour == 0
    assert start_date.minute == 0
    assert start_date.second == 0
    assert start_date.microsecond == 0

    start_date = reporting_period_to_date(ReportingPeriod.THIS_MONTH)
    assert start_date.month == now.month
    assert start_date.day == 1
    assert start_date.hour == 0
    assert start_date.minute == 0
    assert start_date.second == 0
    assert start_date.microsecond == 0


def test_require_pagination(api_client):
    query = """
    query {
        products {
            edges {
                node {
                    name
                }
            }
        }
    }
    """
    response = api_client.post_graphql(query)
    content = _get_graphql_content_from_response(response)
    assert 'errors' in content
    assert content['errors'][0]['message'] == (
        'You must provide a `first` or `last` value to properly paginate the '
        '`products` connection.')


def test_total_count_query(api_client, product):
    query = """
    query {
        products {
            totalCount
        }
    }
    """
    response = api_client.post_graphql(query)
    content = get_graphql_content(response)
    assert content['data']['products']['totalCount'] == Product.objects.count()


def test_mutation_decimal_input(
        staff_api_client, variant, permission_manage_products):
    query = """
    mutation decimalInput($id: ID!, $cost: Decimal) {
        productVariantUpdate(id: $id,
        input: {costPrice: $cost}) {
            errors {
                field
                message
            }
            productVariant {
                costPrice{
                    amount
                }
            }
        }
    }
    """
    variables = {
        'id': graphene.Node.to_global_id('ProductVariant', variant.id),
        'cost': 12.12}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productVariantUpdate']
    assert data['errors'] == []


def test_mutation_decimal_input_without_arguments(
        staff_api_client, variant, permission_manage_products):
    query = """
    mutation {
        productVariantUpdate(id: "%(variant_id)s",
        input: {costPrice: "%(cost)s"}) {
            errors {
                field
                message
            }
            productVariant {
                costPrice{
                    amount
                }
            }
        }
    }
    """ % {
        'variant_id': graphene.Node.to_global_id('ProductVariant', variant.id),
        'cost': 12.12
    }
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productVariantUpdate']
    assert data['errors'] == []
