import json
from unittest.mock import Mock, patch

import graphene
import pytest
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import reverse
from django.test import RequestFactory
from graphql_jwt.shortcuts import get_token
from graphql_relay import to_global_id
from tests.utils import get_graphql_content

from saleor.graphql.middleware import jwt_middleware
from saleor.graphql.product.types import Product
from saleor.graphql.utils import (
    filter_by_query_param, generate_query_argument_description, get_nodes)


def test_jwt_middleware(admin_user):
    def get_response(request):
        return HttpResponse()

    rf = RequestFactory()
    middleware = jwt_middleware(get_response)

    # test setting AnonymousUser on unauthorized request to API
    request = rf.get(reverse('api'))
    assert not hasattr(request, 'user')
    middleware(request)
    assert isinstance(request.user, AnonymousUser)

    # test request with proper JWT token authorizes the request to API
    token = get_token(admin_user)
    request = rf.get(reverse('api'), **{'HTTP_AUTHORIZATION': 'JWT %s' % token})
    assert not hasattr(request, 'user')
    middleware(request)
    assert request.user == admin_user


def test_real_query(user_api_client, product):
    product_attr = product.product_type.product_attributes.first()
    category = product.category
    attr_value = product_attr.values.first()
    filter_by = '%s:%s' % (product_attr.slug, attr_value.slug)
    query = '''
    query Root($categoryId: ID!, $sortBy: String, $first: Int, $attributesFilter: [AttributeScalar], $minPrice: Float, $maxPrice: Float) {
        category(id: $categoryId) {
            ...CategoryPageFragmentQuery
            __typename
        }
        attributes(inCategory: $categoryId) {
            edges {
                node {
                    ...ProductFiltersFragmentQuery
                    __typename
                }
            }
        }
    }

    fragment CategoryPageFragmentQuery on Category {
        id
        name
        url
        ancestors {
            edges {
                node {
                    name
                    id
                    url
                    __typename
                }
            }
        }
        children {
            edges {
                node {
                    name
                    id
                    url
                    slug
                    __typename
                }
            }
        }
        products(first: $first, sortBy: $sortBy, attributes: $attributesFilter, price_Gte: $minPrice, price_Lte: $maxPrice) {
            ...ProductListFragmentQuery
            __typename
        }
        __typename
    }

    fragment ProductListFragmentQuery on ProductCountableConnection {
        edges {
            node {
                ...ProductFragmentQuery
                __typename
            }
            __typename
        }
        pageInfo {
            hasNextPage
            __typename
        }
        __typename
    }

    fragment ProductFragmentQuery on Product {
        id
        name
        price {
            amount
            currency
            localized
            __typename
        }
        availability {
            ...ProductPriceFragmentQuery
            __typename
        }
        thumbnailUrl1x: thumbnailUrl(size: "255x255")
        thumbnailUrl2x: thumbnailUrl(size: "510x510")
        url
        __typename
    }

    fragment ProductPriceFragmentQuery on ProductAvailability {
        available
        discount {
            gross {
                amount
                currency
                __typename
            }
            __typename
        }
        priceRange {
            stop {
                gross {
                    amount
                    currency
                    localized
                    __typename
                }
                currency
                __typename
            }
            start {
                gross {
                    amount
                    currency
                    localized
                    __typename
                }
                currency
                __typename
            }
            __typename
        }
        __typename
    }

    fragment ProductFiltersFragmentQuery on ProductAttribute {
        id
        name
        slug
        values {
            id
            name
            slug
            __typename
        }
        __typename
    }
    '''
    response = user_api_client.post(
        reverse('api'), {
            'query': query,
            'variables': json.dumps(
                {
                    'categoryId': graphene.Node.to_global_id(
                        'Category', category.id),
                    'sortBy': 'name',
                    'first': 1,
                    'attributesFilter': [filter_by]})})
    content = get_graphql_content(response)
    assert 'errors' not in content


def test_get_nodes(product_list):
    global_ids = [
        to_global_id('Product', product.pk) for product in product_list]
    # Make sure function works even if duplicated ids are provided
    global_ids.append(to_global_id('Product', product_list[0].pk))
    # Return products corresponding to global ids
    products = get_nodes(global_ids, Product)
    assert products == product_list

    # Raise an error if requested id has no related database object
    nonexistent_item = Mock(type='Product', pk=123)
    nonexistent_item_global_id = to_global_id(
        nonexistent_item.type, nonexistent_item.pk)
    global_ids.append(nonexistent_item_global_id)
    msg = 'There is no node of type {} with pk {}'.format(
        nonexistent_item.type, nonexistent_item.pk)
    with pytest.raises(AssertionError, message=msg):
        get_nodes(global_ids, Product)
    global_ids.pop()

    # Raise an error if one of the node is of wrong type
    invalid_item = Mock(type='test', pk=123)
    invalid_item_global_id = to_global_id(invalid_item.type, invalid_item.pk)
    global_ids.append(invalid_item_global_id)
    with pytest.raises(AssertionError, message='Must receive an Product id.'):
        get_nodes(global_ids, Product)

    # Raise an error if no nodes were found
    global_ids = []
    msg = 'Could not resolve to a nodes with the global id list of {}.'.format(
        global_ids)
    with pytest.raises(Exception, message=msg):
        get_nodes(global_ids, Product)


@patch('saleor.product.models.Product.objects')
def test_filter_by_query_param(qs):
    qs.filter.return_value = qs

    qs = filter_by_query_param(qs, 'test', ['name', 'force'])
    test_kwargs = {'name__icontains': 'test',
                   'force__icontains': 'test'}
    q_objects = Q()
    for q in test_kwargs:
        q_objects |= Q(**{q: test_kwargs[q]})
    # FIXME: django 1.11 fails on called_once_with(q_objects)
    qs.filter.call_count == 1


def test_generate_query_argument_description():
    expected = 'Supported filter parameters:\n* field_1\n* field_2\n'
    field_list = ['field_1', 'field_2']
    assert generate_query_argument_description(field_list) == expected
