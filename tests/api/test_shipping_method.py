import json

import graphene
import pytest
from django.shortcuts import reverse
from tests.utils import get_graphql_content
from saleor.graphql.shipping.types import ShippingMethodTypeEnum
from saleor.shipping import ShippingMethodType


@pytest.fixture
def weight_based_shipping_query():
    """Dummy weight based createShippingPrice query for tests reusability."""
    return """
    mutation createShipipngPrice(
        $type: ShippingMethodTypeEnum, $name: String!, $price: Decimal,
        $shippingZone: ID!, $maximumOrderWeight: WeightScalar,
        $minimumOrderWeight: WeightScalar) {
        shippingPriceCreate(
            input: {
                name: $name, price: $price, shippingZone: $shippingZone,
                minimumOrderWeight:$minimumOrderWeight,
                maximumOrderWeight: $maximumOrderWeight, type: $type}) {
            errors {
                field
                message
            }
            shippingMethod {
                minimumOrderWeight {
                    value
                    unit
                }
                maximumOrderWeight {
                    value
                    unit}}}}
    """


@pytest.fixture
def price_based_shipping_query():
    """Dummy price based createShippingPrice query for tests reusability."""
    return """
        mutation createShipipngPrice(
            $type: ShippingMethodTypeEnum, $name: String!, $price: Decimal,
            $shippingZone: ID!, $minimumOrderPrice: Decimal,
            $maximumOrderPrice: Decimal) {
        shippingPriceCreate(input: {
                name: $name, price: $price, shippingZone: $shippingZone,
                minimumOrderPrice: $minimumOrderPrice,
                maximumOrderPrice: $maximumOrderPrice, type: $type}) {
            errors {
                field
                message
            }
            shippingMethod {
                name
                price {
                    amount
                }
                minimumOrderPrice {
                    amount
                }
                maximumOrderPrice {
                    amount
                }
                type}}}
    """


def test_shipping_zone_query(user_api_client, shipping_zone):
    shipping = shipping_zone
    query = """
    query ShippingQuery($id: ID!) {
        shippingZone(id: $id) {
            name
            shippingMethods {
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
    no_ppc = shipping_zone.shipping_methods.count()
    assert len(shipping_data['shippingMethods']) == no_ppc
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


@pytest.mark.parametrize(
    'min_price, max_price, expected_min_price, expected_max_price',
    (
        ('10', '15', {'amount': float(10)}, {'amount': float(15)}),
        ('10', None, {'amount': float(10)}, None)))
def test_create_shipping_method(
        admin_api_client, shipping_zone, min_price, max_price,
        expected_min_price, expected_max_price, price_based_shipping_query):
    query = price_based_shipping_query
    name = 'DHL'
    price = '12.34'
    shipping_zone_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_zone.pk)
    variables = json.dumps({
        'shippingZone': shipping_zone_id, 'name': name, 'price': price,
        'minimumOrderPrice': min_price, 'maximumOrderPrice': max_price,
        'type': ShippingMethodTypeEnum.PRICE_BASED.name})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingPriceCreate']['shippingMethod']
    assert 'errors' not in data
    assert data['name'] == name
    assert data['price']['amount'] == float(price)
    assert data['minimumOrderPrice'] == expected_min_price
    assert data['maximumOrderPrice'] == expected_max_price
    assert data['type'] == ShippingMethodType.PRICE_BASED.upper()


@pytest.mark.parametrize(
    'min_weight, max_weight, expected_min_weight, expected_max_weight',
    (
        ('10', '15', {'value': 10, 'unit': 'kg'},
         {'value': 15, 'unit': 'kg'}),
        ('10', None, {'value': 10, 'unit': 'kg'}, None)))
def test_create_weight_based_shipping_method(
        shipping_zone, admin_api_client, min_weight, max_weight,
        expected_min_weight, expected_max_weight, weight_based_shipping_query):
    query = weight_based_shipping_query
    shipping_zone_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_zone.pk)
    variables = json.dumps({
        'shippingZone': shipping_zone_id, 'name': 'DHL', 'price': '12.34',
        'minimumOrderWeight': min_weight, 'maximumOrderWeight': max_weight,
        'type': ShippingMethodTypeEnum.WEIGHT_BASED.name})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingPriceCreate']['shippingMethod']
    assert data['minimumOrderWeight'] == expected_min_weight
    assert data['maximumOrderWeight'] == expected_max_weight


@pytest.mark.parametrize(
    'min_weight, max_weight, expected_error',
    (
        (None, 15, {
            'field': 'minimumOrderWeight',
            'message': 'Minimum order weight is required for'
                       ' Weight Based shipping.'}),
        (20, 15, {
            'field': 'maximumOrderWeight',
            'message': 'Maximum order weight should be larger than the minimum.'  # noqa
        })))
def test_create_weight_shipping_method_errors(
        shipping_zone, admin_api_client, min_weight, max_weight,
        expected_error, weight_based_shipping_query):
    query = weight_based_shipping_query
    shipping_zone_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_zone.pk)
    variables = json.dumps({
        'shippingZone': shipping_zone_id, 'name': 'DHL', 'price': '12.34',
        'minimumOrderWeight': min_weight, 'maximumOrderWeight': max_weight,
        'type': ShippingMethodTypeEnum.WEIGHT_BASED.name})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingPriceCreate']
    assert data['errors'][0] == expected_error


@pytest.mark.parametrize(
    'min_price, max_price, expected_error',
    (
        (None, 15, {
            'field': 'minimumOrderPrice',
            'message': 'Minimum order price is required'
                       ' for Price Based shipping.'}),
        (20, 15, {
            'field': 'maximumOrderPrice',
            'message': 'Maximum order price should be larger than the minimum.'
        })))
def test_create_price_shipping_method_errors(
        shipping_zone, admin_api_client, min_price, max_price,
        expected_error, price_based_shipping_query):
    query = price_based_shipping_query
    shipping_zone_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_zone.pk)
    variables = json.dumps({
        'shippingZone': shipping_zone_id, 'name': 'DHL', 'price': '12.34',
        'minimumOrderPrice': min_price, 'maximumOrderPrice': max_price,
        'type': ShippingMethodTypeEnum.PRICE_BASED.name})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingPriceCreate']
    assert data['errors'][0] == expected_error


def test_update_shipping_method(admin_api_client, shipping_zone):
    query = """
    mutation updateShippingPrice(
        $id: ID!, $price: Decimal, $shippingZone: ID!,
        $type: ShippingMethodTypeEnum!, $minimumOrderPrice: Decimal) {
        shippingPriceUpdate(
            id: $id, input: {
                price: $price, shippingZone: $shippingZone,
                type: $type, minimumOrderPrice: $minimumOrderPrice}) {
            errors {
                field
                message
            }
            shippingMethod {
                price {
                    amount
                }
                minimumOrderPrice {
                    amount
                }
                type
            }
        }
    }
    """
    shipping_method = shipping_zone.shipping_methods.first()
    price = '12.34'
    assert not str(shipping_method.price) == price
    shipping_zone_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        'ShippingMethod', shipping_method.pk)
    variables = json.dumps(
        {
            'shippingZone': shipping_zone_id,
            'price': price,
            'id': shipping_method_id,
            'minimumOrderPrice': '12.00',
            'type': ShippingMethodTypeEnum.PRICE_BASED.name})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shippingPriceUpdate']['shippingMethod']
    assert data['price']['amount'] == float(price)


def test_delete_shipping_method(admin_api_client, shipping_method):
    query = """
        mutation deleteShippingPrice($id: ID!) {
            shippingPriceDelete(id: $id) {
                shippingMethod {
                    price {
                        amount
                    }
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
    data = content['data']['shippingPriceDelete']['shippingMethod']
    assert data['price']['amount'] == float(shipping_method.price)
    with pytest.raises(shipping_method._meta.model.DoesNotExist):
        shipping_method.refresh_from_db()
