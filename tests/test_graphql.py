import json

import graphene
import pytest

from saleor.dashboard.category.forms import CategoryForm
from saleor.product.models import Category, Product, ProductAttribute


def get_content(response):
    return json.loads(response.content.decode('utf8'))


def test_category_query(client, product_in_stock):
    category = Category.objects.first()
    query = '''
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
    ''' % {'category_pk': graphene.Node.to_global_id('Category', category.pk)}
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


def test_fetch_all_products(client, product_in_stock):
    query = '''
    query {
        products {
            totalCount
            edges {
                node {
                    id
                }
            }
        }
    }
    '''
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert 'errors' not in content
    num_products = Product.objects.count()
    assert content['data']['products']['totalCount'] == num_products
    assert len(content['data']['products']['edges']) == num_products


@pytest.mark.djangodb
def test_fetch_unavailable_products(client, product_in_stock):
    Product.objects.update(is_published=False)
    query = '''
    query {
        products {
            totalCount
            edges {
                node {
                    id
                }
            }
        }
    }
    '''
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert 'errors' not in content
    assert content['data']['products']['totalCount'] == 0
    assert not content['data']['products']['edges']


def test_product_query(client, product_in_stock):
    category = Category.objects.first()
    product = category.products.first()
    query = '''
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
    ''' % {'category_id': graphene.Node.to_global_id('Category', category.id)}
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
    query = '''
    query getProducts($categoryId: ID) {
        products(category: $categoryId) {
            edges {
                node {
                    name
                }
            }
        }
    }
    '''
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
    query = '''
    query ($productId: ID!) {
        node(id: $productId) {
            ... on Product {
                name
            }
        }
    }
    '''
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
    filter_by = '%s:%s' % (product_attr.slug, attr_value.slug)
    query = '''
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
    ''' % {
        'category_id': graphene.Node.to_global_id('Category', category.id),
        'filter_by': filter_by}
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert 'errors' not in content
    product_data = content['data']['category']['products']['edges'][0]['node']
    assert product_data['name'] == product_in_stock.name


def test_attributes_query(client, product_in_stock):
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
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert 'errors' not in content
    attributes_data = content['data']['attributes']['edges']
    assert len(attributes_data) == attributes.count()


def test_attributes_in_category_query(client, product_in_stock):
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
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert 'errors' not in content
    attributes_data = content['data']['attributes']['edges']
    assert len(attributes_data) == ProductAttribute.objects.count()


def test_real_query(client, product_in_stock):
    category = product_in_stock.category
    product_attr = product_in_stock.product_type.product_attributes.first()
    category = product_in_stock.category
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
            currency
            gross
            grossLocalized
            net
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
            gross
            __typename
        }
        priceRange {
            maxPrice {
                gross
                grossLocalized
                currency
                __typename
            }
            minPrice {
                gross
                grossLocalized
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
            color
            __typename
        }
        __typename
    }
    '''
    response = client.post(
        '/graphql/', {
            'query': query,
            'variables': json.dumps(
                {
                    'categoryId': graphene.Node.to_global_id(
                        'Category', category.id),
                    'sortBy': 'name',
                    'first': 1,
                    'attributesFilter': [filter_by]})})
    content = get_content(response)
    assert 'errors' not in content


def test_category_create_mutation(client):
    query = """
        mutation($name: String, $description: String, $parent: Int) {
            categoryCreate(data: {
                name: $name
                description: $description
                parent: $parent}
            ) {
                category {
                    pk
                    name
                    slug
                    description
                    parent {
                        pk
                    }
                }
                errors {
                    field
                    message
                }
            }
        }
    """

    category_name = 'Test category'
    category_description = 'Test description'

    # test creating root category
    variables = json.dumps({
        'name': category_name, 'description': category_description})
    response = client.post(
        '/graphql/', {'query': query, 'variables': variables})
    content = get_content(response)
    assert 'errors' not in content
    data = content['data']['categoryCreate']
    assert data['errors'] == []
    assert data['category']['name'] == category_name
    assert data['category']['description'] == category_description
    assert not data['category']['parent']

    # test creating subcategory
    parent_pk = data['category']['pk']
    variables = json.dumps({
        'name': category_name, 'description': category_description,
        'parent': int(parent_pk)})
    response = client.post(
        '/graphql/', {'query': query, 'variables': variables})
    content = get_content(response)
    assert 'errors' not in content
    data = content['data']['categoryCreate']
    assert data['errors'] == []
    assert data['category']['parent']['pk'] == parent_pk


def test_category_update_mutation(client, default_category):
    query = """
        mutation($pk: Int, $name: String, $description: String, $parent: Int) {
            categoryUpdate(
                pk: $pk,
                data: {
                    name: $name
                    description: $description
                    parent: $parent}
            ) {
                category {
                    pk
                    name
                    slug
                    description
                    parent {
                        pk
                    }
                }
                errors {
                    field
                    message
                }
            }
        }
    """

    category_name = 'Updated name'
    category_description = 'Updated description'

    # test creating root category
    variables = json.dumps({
        'name': category_name, 'description': category_description,
        'pk': default_category.pk})
    response = client.post(
        '/graphql/', {'query': query, 'variables': variables})
    content = get_content(response)
    assert 'errors' not in content
    data = content['data']['categoryUpdate']
    assert data['errors'] == []
    assert data['category']['pk'] == str(default_category.pk)
    assert data['category']['name'] == category_name
    assert data['category']['description'] == category_description
    assert not data['category']['parent']


def test_category_delete_mutation(client, default_category):
    query = """
        mutation($pk: Int) {
            categoryDelete(pk: $pk) {
                category {
                    name
                    pk
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    variables = json.dumps({'pk': default_category.pk})
    response = client.post(
        '/graphql/', {'query': query, 'variables': variables})
    content = get_content(response)
    assert 'errors' not in content
    data = content['data']['categoryDelete']
    assert data['category']['pk'] is None
    assert data['category']['name'] == default_category.name
