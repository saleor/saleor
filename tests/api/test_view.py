import graphene
import pytest
from django.test import override_settings

from .conftest import API_PATH
from .utils import _get_graphql_content_from_response, get_graphql_content


def test_batch_queries(category, product, api_client):
    query_product = """
        query GetProduct($id: ID!) {
            product(id: $id) {
                name
            }
        }
    """
    query_category = """
        query GetCategory($id: ID!) {
            category(id: $id) {
                name
            }
        }
    """
    data = [
        {'query': query_category, 'variables': {
            'id': graphene.Node.to_global_id('Category', category.pk)}},
        {'query': query_product, 'variables': {
            'id': graphene.Node.to_global_id('Product', product.pk)}}]
    response = api_client.post(data)
    batch_content = get_graphql_content(response)
    assert 'errors' not in batch_content
    assert isinstance(batch_content, list)
    assert len(batch_content) == 2

    data = {
        field: value
        for content in batch_content
        for field, value in content['data'].items()}
    assert data['product']['name'] == product.name
    assert data['category']['name'] == category.name


def test_graphql_view_get_in_non_debug_mode(client):
    response = client.get(API_PATH)
    assert response.status_code == 405


@override_settings(DEBUG=True)
def test_graphql_view_get_in_debug_mode(client):
    response = client.get(API_PATH)
    assert response.status_code == 200
    assert response.templates[0].name == 'graphql/playground.html'


def test_graphql_view_options(client):
    response = client.options(API_PATH)
    assert response.status_code == 200


@pytest.mark.parametrize('method', ('put', 'patch', 'delete'))
def test_graphql_view_not_allowed(method, client):
    func = getattr(client, method)
    response = func(API_PATH)
    assert response.status_code == 405


def test_invalid_request_body(client):
    data = 'invalid-data'
    response = client.post(API_PATH, data, content_type='application/json')
    assert response.status_code == 400
    content = _get_graphql_content_from_response(response)
    assert 'errors' in content


def test_invalid_query(api_client):
    query = 'query { invalid }'
    response = api_client.post_graphql(query, check_no_permissions=False)
    assert response.status_code == 400
    content = _get_graphql_content_from_response(response)
    assert 'errors' in content


def test_no_query(client):
    response = client.post(API_PATH, '', content_type='application/json')
    assert response.status_code == 400
    content = _get_graphql_content_from_response(response)
    assert content['errors'][0]['message'] == 'Must provide a query string.'


def test_graphql_execution_exception(monkeypatch, api_client):
    def mocked_execute(*args, **kwargs):
        raise IOError('Spanish inquisition')

    monkeypatch.setattr(
        'graphql.backend.core.execute_and_validate', mocked_execute)
    response = api_client.post_graphql('{ shop { name }}')
    assert response.status_code == 400
    content = _get_graphql_content_from_response(response)
    assert content['errors'][0]['message'] == 'Spanish inquisition'
