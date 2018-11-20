import graphene

from .utils import get_graphql_content


def test_batch_queries(category, product, staff_api_client):
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
    response = staff_api_client.post(data)
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
