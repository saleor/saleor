import json

import graphene
import pytest
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
                edges {
                    node {
                        countryCode
                    }
                }
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
    data_price_range = shipping_data['priceRange']
    assert data_price_range['start']['amount'] == price_range.start.amount
    assert data_price_range['stop']['amount'] == price_range.stop.amount


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


def test_create_shipping_method(admin_api_client):
    query = """
        mutation createShipping{
            shippingMethodCreate(
                input: {name: "test shipping", description: "test desc"}) {
                    shippingMethod {
                        name
                        description
                    }
            }
        }
    """
    response = admin_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingMethodCreate']['shippingMethod']
    assert data['name'] == 'test shipping'
    assert data['description'] == 'test desc'


def test_update_shipping_method(admin_api_client, shipping_method):
    query = """
        mutation updateShipping($id: ID!, $name: String) {
            shippingMethodUpdate(id: $id, input: {name: $name}) {
                shippingMethod {
                    name
                }
            }
        }
    """
    name = 'Parabolic name'
    shipping_id = graphene.Node.to_global_id(
        'ShippingMethod', shipping_method.pk)
    assert shipping_method.name != name
    variables = json.dumps({'id': shipping_id, 'name': name})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingMethodUpdate']['shippingMethod']
    assert data['name'] == name


def test_delete_shipping_method(admin_api_client, shipping_method):
    query = """
        mutation deleteShippingMethod($id: ID!) {
            shippingMethodDelete(id: $id) {
                shippingMethod {
                    name
                }
            }
        }
    """
    shipping_method_id = graphene.Node.to_global_id(
        'ShippingMethod', shipping_method.pk)
    variables = json.dumps({'id': shipping_method_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingMethodDelete']['shippingMethod']
    assert data['name'] == shipping_method.name
    with pytest.raises(shipping_method._meta.model.DoesNotExist):
        shipping_method.refresh_from_db()


def test_create_shipping_price(admin_api_client, shipping_method):
    query = """
    mutation createShippingPrice(
        $code: String!, $price: Decimal, $shippingMethod: ID!){
        shippingPriceCreate(
            input: {
                countryCode: $code, price: $price,
                shippingMethod: $shippingMethod}) {
            shippingMethodCountry {
                countryCode
                price {
                    amount
                }
            }
        }
    }
    """
    code = 'PL'
    price = '12.34'
    shipping_method_id = graphene.Node.to_global_id(
        'ShippingMethod', shipping_method.pk)
    variables = json.dumps(
        {
            'shippingMethod': shipping_method_id,
            'code': code,
            'price': price})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingPriceCreate']['shippingMethodCountry']
    assert data['countryCode'] == code
    assert data['price']['amount'] == float(price)


def test_update_shipping_price(admin_api_client, shipping_method, shipping_price):
    query = """
    mutation updateShippingPrice(
        $id: ID!, $price: Decimal, $shippingMethod: ID!) {
        shippingPriceUpdate(
            id: $id, input: {price: $price, shippingMethod: $shippingMethod}) {
            shippingMethodCountry {
                price {
                    amount
                }
            }
        }
    }
    """
    # shipping_price = shipping_method.price_per_country.first()
    price = '12.34'
    assert not str(shipping_price.price) == price
    shipping_method_id = graphene.Node.to_global_id(
        'ShippingMethod', shipping_method.pk)
    shipping_price_id = graphene.Node.to_global_id(
        'ShippingMethodCountry', shipping_price.pk)
    variables = json.dumps(
        {
            'shippingMethod': shipping_method_id,
            'price': price,
            'id': shipping_price_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingPriceUpdate']['shippingMethodCountry']
    assert data['price']['amount'] == float(price)


def test_delete_shipping_price(admin_api_client, shipping_price):
    query = """
        mutation deleteShippingPrice($id: ID!) {
            shippingPriceDelete(id: $id) {
                shippingMethodCountry {
                    countryCode
                }
            }
        }
        """
    shipping_price_id = graphene.Node.to_global_id(
        'ShippingMethodCountry', shipping_price.pk)
    variables = json.dumps({'id': shipping_price_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingPriceDelete']['shippingMethodCountry']
    assert data['countryCode'] == shipping_price.country_code
    with pytest.raises(shipping_price._meta.model.DoesNotExist):
        shipping_price.refresh_from_db()
