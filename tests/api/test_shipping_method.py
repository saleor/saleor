import json

import graphene
import pytest
from django.shortcuts import reverse
from tests.utils import get_graphql_content


def test_shipping_zone_query(user_api_client, shipping_zone):
    shipping = shipping_zone
    query = """
    query ShippingQuery($id: ID!) {
        shippingZone(id: $id) {
            name
            shippingRates {
                edges {
                    node {
                        price {
                            amount
                        }
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

    ID = graphene.Node.to_global_id('ShippingZone', shipping.id)
    variables = json.dumps({'id': ID})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)

    shipping_data = content['data']['shippingZone']
    assert 'errors' not in content
    assert shipping_data['name'] == shipping.name
    no_ppc = shipping_zone.shipping_rates.count()
    assert len(shipping_data['shippingRates']) == no_ppc
    price_range = shipping.price_range
    data_price_range = shipping_data['priceRange']
    assert data_price_range['start']['amount'] == price_range.start.amount
    assert data_price_range['stop']['amount'] == price_range.stop.amount


def test_shipping_zones_query(user_api_client, shipping_zone):
    query = """
    query MultipleShippings {
        shippingZones {
            totalCount
        }
    }
    """
    num_of_shippings = shipping_zone._meta.model.objects.count()

    response = user_api_client.post(
        reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    assert content['data']['shippingZones']['totalCount'] == num_of_shippings


def test_create_shipping_zone(admin_api_client):
    query = """
        mutation createShipping{
            shippingZoneCreate(
                input: {name: "test shipping", countries: ["PL"]}) {
                    shippingZone {
                        name
                        countries
                    }
                }
        }
    """
    response = admin_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingZoneCreate']['shippingZone']
    assert data['name'] == 'test shipping'
    assert data['countries'] == ['PL']


def test_update_shipping_zone(admin_api_client, shipping_zone):
    query = """
        mutation updateShipping($id: ID!, $name: String) {
            shippingZoneUpdate(id: $id, input: {name: $name}) {
                shippingZone {
                    name
                }
            }
        }
    """
    name = 'Parabolic name'
    shipping_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_zone.pk)
    assert shipping_zone.name != name
    variables = json.dumps(
        {'id': shipping_id, 'name': name})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingZoneUpdate']['shippingZone']
    assert data['name'] == name


def test_delete_shipping_zone(admin_api_client, shipping_zone):
    query = """
        mutation deleteShippingZone($id: ID!) {
            shippingZoneDelete(id: $id) {
                shippingZone {
                    name
                }
            }
        }
    """
    shipping_zone_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_zone.pk)
    variables = json.dumps({'id': shipping_zone_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingZoneDelete']['shippingZone']
    assert data['name'] == shipping_zone.name
    with pytest.raises(shipping_zone._meta.model.DoesNotExist):
        shipping_zone.refresh_from_db()


def test_create_shipping_rate(admin_api_client, shipping_zone):
    query = """
    mutation createShippingPrice(
        $name: String!, $price: Decimal, $shippingZone: ID!){
        shippingPriceCreate(
            input: {
                name: $name, price: $price,
                shippingZone: $shippingZone}) {
            shippingRate {
                name
                price {
                    amount
                }
            }
        }
    }
    """
    name = 'DHL'
    price = '12.34'
    shipping_zone_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_zone.pk)
    variables = json.dumps(
        {
            'shippingZone': shipping_zone_id,
            'name': name,
            'price': price})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingPriceCreate']['shippingRate']
    assert data['name'] == name
    assert data['price']['amount'] == float(price)


def test_update_shipping_rate(admin_api_client, shipping_zone, shipping_rate):
    query = """
    mutation updateShippingPrice(
        $id: ID!, $price: Decimal, $shippingZone: ID!) {
        shippingPriceUpdate(
            id: $id, input: {price: $price, shippingZone: $shippingZone}) {
            shippingRate {
                price {
                    amount
                }
            }
        }
    }
    """
    # shipping_rate = shipping_zone.shipping_rates.first()
    price = '12.34'
    assert not str(shipping_rate.price) == price
    shipping_zone_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_zone.pk)
    shipping_rate_id = graphene.Node.to_global_id(
        'ShippingRate', shipping_rate.pk)
    variables = json.dumps(
        {
            'shippingZone': shipping_zone_id,
            'price': price,
            'id': shipping_rate_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingPriceUpdate']['shippingRate']
    assert data['price']['amount'] == float(price)


def test_delete_shipping_rate(admin_api_client, shipping_rate):
    query = """
        mutation deleteShippingPrice($id: ID!) {
            shippingPriceDelete(id: $id) {
                shippingRate {
                    price {
                        amount
                    }
                }
            }
        }
        """
    shipping_rate_id = graphene.Node.to_global_id(
        'ShippingRate', shipping_rate.pk)
    variables = json.dumps({'id': shipping_rate_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingPriceDelete']['shippingRate']
    assert data['price']['amount'] == float(shipping_rate.price)
    with pytest.raises(shipping_rate._meta.model.DoesNotExist):
        shipping_rate.refresh_from_db()
