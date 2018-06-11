import json

import graphene
from django.shortcuts import reverse
from tests.utils import get_graphql_content


def test_shipping_method_query(user_api_client, shipping_method):
    shipping = shipping_method
    query = """
    query ShppingQuery($id: ID!) {
        shippingMethod(id: $id) {
            name
            description
            pricePerCountry {
                countryCode
            }
            priceRange {
                start {
                    amount
                }
                stop {
                    amount
                }
            }
        }
    }
    """

    ID = graphene.Node.to_global_id('ShippingMethod', shipping.id)
    variables = json.dumps({'id': ID})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    shipping_data = content['data']['shippingMethod']

    assert 'errors' not in content
    assert shipping_data['name'] == shipping.name
    assert shipping_data['description'] == shipping.description
    no_ppc = shipping_method.price_per_country.count()
    assert len(shipping_data['pricePerCountry']) == no_ppc
    price_range = shipping.price_range
    assert shipping_data[
               'priceRange']['start']['amount'] == price_range.start.amount
    assert shipping_data[
               'priceRange']['stop']['amount'] == price_range.stop.amount


def test_shipping_methods_query(user_api_client, shipping_method):
    query = """
    query MultipleShippings {
        shippingMethods {
            totalCount
        }
    }
    """
    no_shippings = shipping_method._meta.model.objects.count()

    response = user_api_client.post(
        reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    assert content['data']['shippingMethods']['totalCount'] == no_shippings
