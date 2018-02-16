import json

import graphene
import pytest

from saleor.product.models import Category, ProductAttribute


def get_content(response):
    return json.loads(response.content.decode('utf8'))


def test_category_query(client, product_in_stock):
    category = Category.objects.first()
    query = """
        query {
            category(id: "%(category_pk)s") {
                id
                name
                productsCount
                ancestors {
                    edges {
                        node {
                            name
                        }
                    }
                }
                children {
                    edges {
                        node {
                            name
                        }
                    }
                }
                siblings {
                    edges {
                        node {
                            name
                        }
                    }
                }
            }
        }
    """ % {'category_pk': graphene.Node.to_global_id('Category', category.pk)}
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert 'errors' not in content
    category_data = content['data']['category']
    assert category_data is not None
    assert category_data['name'] == category.name
    assert category_data['productsCount'] == category.products.count()
    assert (
        len(category_data['ancestors']['edges']) ==
        category.get_ancestors().count())
    assert (
        len(category_data['children']['edges']) ==
        category.get_children().count())
    assert (
        len(category_data['siblings']['edges']) ==
        category.get_siblings().count())


def test_product_query(client, product_in_stock):
    category = Category.objects.first()
    product = category.products.first()
    query = """
        query {
            category(id: "%(category_id)s") {
                products {
                    edges {
                        node {
                            id
                            name
                            url
                            thumbnailUrl
                            images { url }
                            variants {
                                name
                                stockQuantity
                            }
                            availability {
                                available,
                                priceRange {
                                    minPrice {
                                        gross
                                        net
                                        currency
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    """ % {'category_id': graphene.Node.to_global_id('Category', category.id)}
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert 'errors' not in content
    assert content['data']['category'] is not None
    product_edges_data = content['data']['category']['products']['edges']
    assert len(product_edges_data) == category.products.count()
    product_data = product_edges_data[0]['node']
    assert product_data['name'] == product.name
    assert product_data['url'] == product.get_absolute_url()
    gross = product_data['availability']['priceRange']['minPrice']['gross']
    assert float(gross) == float(product.price.gross)


def test_filter_product_by_category(client, product_in_stock):
    category = product_in_stock.category
    query = """
        query getProducts($categoryId: ID) {
            products(category: $categoryId) {
                edges {
                    node {
                        name
                    }
                }
            }
        }
    """
    response = client.post(
        '/graphql/',
        {
            'query': query,
            'variables': json.dumps(
                {
                    'categoryId': graphene.Node.to_global_id(
                        'Category', category.id)}),
            'operationName': 'getProducts'})
    content = get_content(response)
    assert 'errors' not in content
    product_data = content['data']['products']['edges'][0]['node']
    assert product_data['name'] == product_in_stock.name


def test_fetch_product_by_id(client, product_in_stock):
    query = """
        query ($productId: ID!) {
            node(id: $productId) {
                ... on Product {
                    name
                }
            }
        }
    """
    response = client.post(
        '/graphql/',
        {
            'query': query,
            'variables': json.dumps(
                {
                    'productId': graphene.Node.to_global_id(
                        'Product', product_in_stock.id)})})
    content = get_content(response)
    assert 'errors' not in content
    product_data = content['data']['node']
    assert product_data['name'] == product_in_stock.name


def test_filter_product_by_attributes(client, product_in_stock):
    product_attr = product_in_stock.product_type.product_attributes.first()
    category = product_in_stock.category
    attr_value = product_attr.values.first()
    filter_by = "%s:%s" % (product_attr.slug, attr_value.slug)
    query = """
        query {
            category(id: "%(category_id)s") {
                products(attributes: ["%(filter_by)s"]) {
                    edges {
                        node {
                            name
                        }
                    }
                }
            }
        }
    """ % {
        'category_id': graphene.Node.to_global_id('Category', category.id),
        'filter_by': filter_by}
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert 'errors' not in content
    product_data = content['data']['category']['products']['edges'][0]['node']
    assert product_data['name'] == product_in_stock.name


def test_attributes_query(client, product_in_stock):
    attributes = ProductAttribute.objects.prefetch_related('values')
    query = """
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
    """
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert 'errors' not in content
    attributes_data = content['data']['attributes']['edges']
    assert len(attributes_data) == attributes.count()


def test_attributes_in_category_query(client, product_in_stock):
    category = Category.objects.first()
    query = """
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
    """ % {'category_id': graphene.Node.to_global_id('Category', category.id)}
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert 'errors' not in content
    attributes_data = content['data']['attributes']['edges']
    assert len(attributes_data) == ProductAttribute.objects.count()
