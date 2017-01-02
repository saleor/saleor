import json
import pytest

from saleor.product.models import Category


def assert_success_response(content):
    assert 'errors' not in content
    assert 'data' in content
    assert 'viewer' in content['data']


def assert_corresponding_categories(data, queryset):
    assert type(data) == list
    assert len(data) == queryset.count()
    for (category_data, category) in zip(data, queryset):
        assert category_data['name'] == category.name


@pytest.mark.django_db()
def test_category_query(client, product_in_stock):
    category = Category.objects.first()
    query = """
        query {
            viewer {
                category(pk: %(category_pk)s) {
                    pk
                    name
                    productsCount
                    ancestors { name }
                    children { name }
                    siblings { name }
                }
            }
        }
    """ % {'category_pk': category.pk}
    response = client.post('/graphql/', {'query': query})
    content = json.loads(response.content)
    assert_success_response(content)
    category_data = content['data']['viewer']['category']
    assert category_data is not None
    assert int(category_data['pk']) == category.pk
    assert category_data['name'] == category.name
    assert category_data['productsCount'] == category.products.count()
    assert_corresponding_categories(
        category_data['ancestors'], category.get_ancestors())
    assert_corresponding_categories(
        category_data['children'], category.get_children())
    assert_corresponding_categories(
        category_data['siblings'], category.get_siblings())


@pytest.mark.django_db()
def test_product_query(client, product_in_stock):
    category = Category.objects.first()
    product = category.products.first()
    query = """
        query {
            viewer {
                category(pk: %(category_pk)s) {
                    products {
                        edges {
                            node {
                                pk
                                name
                                url
                                imageUrl
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
                                        }
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
    content = json.loads(response.content)
    assert_success_response(content)
    assert content['data']['viewer']['category'] is not None
    product_edges_data = content['data']['viewer']['category']['products']['edges']
    assert len(product_edges_data) == category.products.count()
    product_data = product_edges_data[0]['node']
    assert int(product_data['pk']) == product.pk
    assert product_data['name'] == product.name
    assert product_data['url'] == product.get_absolute_url()
