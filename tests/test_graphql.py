import json

import pytest

from saleor.product.models import Category, ProductAttribute


def get_content(response):
    return json.loads(response.content.decode('utf8'))


def assert_success(content):
    assert 'errors' not in content
    assert 'data' in content


def assert_corresponding_fields(iterable_data, queryset, fields):
    assert len(iterable_data) == queryset.count()
    for (data, obj) in zip(iterable_data, queryset):
        for field in fields:
            assert str(data[field]) == str(getattr(obj, field))


@pytest.mark.django_db()
def test_category_query(client, product_in_stock):
    category = Category.objects.first()
    query = """
        query {
            category(pk: %(category_pk)s) {
                pk
                name
                productsCount
                ancestors { name }
                children { name }
                siblings { name }
            }
        }
    """ % {'category_pk': category.pk}
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert_success(content)
    category_data = content['data']['category']
    assert category_data is not None
    assert int(category_data['pk']) == category.pk
    assert category_data['name'] == category.name
    assert category_data['productsCount'] == category.products.count()
    assert_corresponding_fields(
        category_data['ancestors'], category.get_ancestors(), ['name'])
    assert_corresponding_fields(
        category_data['children'], category.get_children(), ['name'])
    assert_corresponding_fields(
        category_data['siblings'], category.get_siblings(), ['name'])


@pytest.mark.django_db()
def test_product_query(client, product_in_stock):
    category = Category.objects.first()
    product = category.products.first()
    query = """
        query {
            category(pk: %(category_pk)s) {
                products {
                    edges {
                        node {
                            pk
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
    """ % {'category_pk': category.pk}
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert_success(content)
    assert content['data']['category'] is not None
    product_edges_data = content['data']['category']['products']['edges']
    assert len(product_edges_data) == category.products.count()
    product_data = product_edges_data[0]['node']
    assert int(product_data['pk']) == product.pk
    assert product_data['name'] == product.name
    assert product_data['url'] == product.get_absolute_url()
    gross = product_data['availability']['priceRange']['minPrice']['gross']
    assert float(gross) == float(product.price.gross)


@pytest.mark.django_db()
def test_filter_product_by_attributes(client, product_in_stock):
    category = Category.objects.first()
    product_attr = product_in_stock.product_type.product_attributes.first()
    attr_value = product_attr.values.first()
    filter_by = "%s:%s" % (product_attr.name, attr_value.slug)
    query = """
        query {
            category(pk: %(category_pk)s) {
                products(attributes: ["%(filter_by)s"]) {
                    edges {
                        node {
                            name
                        }
                    }
                }
            }
        }
    """ % {'category_pk': category.pk, 'filter_by': filter_by}
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert_success(content)
    product_data = content['data']['category']['products']['edges'][0]['node']
    assert product_data['name'] == product_in_stock.name


@pytest.mark.django_db()
def test_attributes_query(client, product_in_stock):
    attributes = ProductAttribute.objects.prefetch_related('values')
    query = """
        query {
            attributes {
                pk
                name
                slug
                values {
                    pk
                    name
                    slug
                }
            }
        }
    """
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert_success(content)
    attributes_data = content['data']['attributes']
    assert_corresponding_fields(attributes_data, attributes, ['pk', 'name'])


@pytest.mark.django_db()
def test_attributes_in_category_query(client, product_in_stock):
    category = Category.objects.first()
    query = """
        query {
            attributes(categoryPk: %(category_pk)s) {
                pk
                name
                slug
                values {
                    pk
                    name
                    slug
                }
            }
        }
    """ % {'category_pk': category.pk}
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert_success(content)
