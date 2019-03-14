import graphene
import pytest

from saleor.graphql.shipping.types import ShippingMethodTypeEnum
from tests.api.utils import get_graphql_content


def test_shipping_zone_query(
        staff_api_client, shipping_zone, permission_manage_shipping):
    shipping = shipping_zone
    query = """
    query ShippingQuery($id: ID!) {
        shippingZone(id: $id) {
            name
            shippingMethods {
                price {
                    amount
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
    variables = {'id': ID}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)

    shipping_data = content['data']['shippingZone']
    assert shipping_data['name'] == shipping.name
    num_of_shipping_methods = shipping_zone.shipping_methods.count()
    assert len(shipping_data['shippingMethods']) == num_of_shipping_methods
    price_range = shipping.price_range
    data_price_range = shipping_data['priceRange']
    assert data_price_range['start']['amount'] == price_range.start.amount
    assert data_price_range['stop']['amount'] == price_range.stop.amount


def test_shipping_zones_query(
        staff_api_client, shipping_zone, permission_manage_shipping):
    query = """
    query MultipleShippings {
        shippingZones {
            totalCount
        }
    }
    """
    num_of_shippings = shipping_zone._meta.model.objects.count()
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)
    assert content['data']['shippingZones']['totalCount'] == num_of_shippings


CREATE_SHIPPING_ZONE_QUERY = """
    mutation createShipping(
        $name: String, $default: Boolean, $countries: [String]) {
        shippingZoneCreate(
            input: {name: $name, countries: $countries, default: $default})
        {
            errors {
                field
                message
            }
            shippingZone {
                name
                countries {
                    code
                }
                default
            }
        }
    }
"""


def test_create_shipping_zone(staff_api_client, permission_manage_shipping):
    query = CREATE_SHIPPING_ZONE_QUERY
    variables = {'name': 'test shipping', 'countries': ['PL']}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)
    data = content['data']['shippingZoneCreate']
    assert not data['errors']
    zone = data['shippingZone']
    assert zone['name'] == 'test shipping'
    assert zone['countries'] == [{'code': 'PL'}]
    assert not zone['default']


def test_create_default_shipping_zone(
        staff_api_client, permission_manage_shipping):
    query = CREATE_SHIPPING_ZONE_QUERY
    variables = {'default': True, 'name': 'test shipping', 'countries': ['PL']}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)
    data = content['data']['shippingZoneCreate']
    assert not data['errors']
    zone = data['shippingZone']
    assert zone['name'] == 'test shipping'
    assert zone['countries'] == []
    assert zone['default']


def test_create_duplicated_default_shipping_zone(
        staff_api_client, shipping_zone, permission_manage_shipping):
    shipping_zone.default = True
    shipping_zone.save()

    query = CREATE_SHIPPING_ZONE_QUERY
    variables = {'default': True, 'name': 'test shipping', 'countries': ['PL']}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)
    data = content['data']['shippingZoneCreate']
    assert data['errors']
    assert data['errors'][0]['field'] == 'default'
    assert data['errors'][0]['message'] == (
        'Default shipping zone already exists.')


UPDATE_SHIPPING_ZONE_QUERY = """
    mutation updateShipping(
            $id: ID!, $name: String, $default: Boolean, $countries: [String]) {
        shippingZoneUpdate(
            id: $id,
            input: {name: $name, default: $default, countries: $countries})
        {
            shippingZone {
                name
            }
            errors {
                field
                message
            }
        }
    }
"""


def test_update_shipping_zone(
        staff_api_client, shipping_zone, permission_manage_shipping):
    query = UPDATE_SHIPPING_ZONE_QUERY
    name = 'Parabolic name'
    shipping_id = graphene.Node.to_global_id('ShippingZone', shipping_zone.pk)
    variables = {'id': shipping_id, 'name': name, 'countries': []}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)
    data = content['data']['shippingZoneUpdate']
    assert not data['errors']
    data = content['data']['shippingZoneUpdate']['shippingZone']
    assert data['name'] == name


def test_update_shipping_zone_default_exists(
        staff_api_client, shipping_zone, permission_manage_shipping):
    query = UPDATE_SHIPPING_ZONE_QUERY
    default_zone = shipping_zone
    default_zone.default = True
    default_zone.pk = None
    default_zone.save()
    shipping_zone = shipping_zone.__class__.objects.filter(default=False).get()

    shipping_id = graphene.Node.to_global_id('ShippingZone', shipping_zone.pk)
    variables = {
        'id': shipping_id,
        'name': 'Name',
        'countries': [],
        'default': True}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)
    data = content['data']['shippingZoneUpdate']
    assert data['errors']
    assert data['errors'][0]['field'] == 'default'
    assert data['errors'][0]['message'] == (
        'Default shipping zone already exists.')


def test_delete_shipping_zone(
        staff_api_client, shipping_zone, permission_manage_shipping):
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
    variables = {'id': shipping_zone_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)
    data = content['data']['shippingZoneDelete']['shippingZone']
    assert data['name'] == shipping_zone.name
    with pytest.raises(shipping_zone._meta.model.DoesNotExist):
        shipping_zone.refresh_from_db()


PRICE_BASED_SHIPPING_QUERY = """
    mutation createShippingPrice(
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
        shippingZone {
            id
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
            type
            }
        }
    }
"""


@pytest.mark.parametrize(
    'min_price, max_price, expected_min_price, expected_max_price',
    (
        (10.32, 15.43, {'amount': 10.32}, {'amount': 15.43}),
        (10.33, None, {'amount': 10.33}, None)
    )
)
def test_create_shipping_method(
        staff_api_client, shipping_zone, min_price, max_price,
        expected_min_price, expected_max_price, permission_manage_shipping):
    query = PRICE_BASED_SHIPPING_QUERY
    name = 'DHL'
    price = 12.34
    shipping_zone_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_zone.pk)
    variables = {
        'shippingZone': shipping_zone_id,
        'name': name,
        'price': price,
        'minimumOrderPrice': min_price,
        'maximumOrderPrice': max_price,
        'type': ShippingMethodTypeEnum.PRICE.name}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)
    data = content['data']['shippingPriceCreate']
    assert 'errors' not in data['shippingMethod']
    assert data['shippingMethod']['name'] == name
    assert data['shippingMethod']['price']['amount'] == float(price)
    assert data['shippingMethod']['minimumOrderPrice'] == expected_min_price
    assert data['shippingMethod']['maximumOrderPrice'] == expected_max_price
    assert data['shippingMethod']['type'] == ShippingMethodTypeEnum.PRICE.name
    assert data['shippingZone']['id'] == shipping_zone_id


def test_create_price_shipping_method_errors(
        shipping_zone, staff_api_client, permission_manage_shipping):
    query = PRICE_BASED_SHIPPING_QUERY
    shipping_zone_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_zone.pk)
    variables = {
        'shippingZone': shipping_zone_id,
        'name': 'DHL',
        'price': 12.34,
        'minimumOrderPrice': 20,
        'maximumOrderPrice': 15,
        'type': ShippingMethodTypeEnum.PRICE.name}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)
    data = content['data']['shippingPriceCreate']
    assert (
        data['errors'][0]['message'] ==
        'Maximum order price should be larger than the minimum order price.')


WEIGHT_BASED_SHIPPING_QUERY = """
    mutation createShippingPrice(
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
                    unit
                }
            }
            shippingZone {
                id
            }
        }
    }
"""


@pytest.mark.parametrize(
    'min_weight, max_weight, expected_min_weight, expected_max_weight',
    ((
        10.32, 15.64, {
            'value': 10.32,
            'unit': 'kg'}, {
                'value': 15.64,
                'unit': 'kg'}),
     (10.92, None, {
         'value': 10.92,
         'unit': 'kg'}, None)))
def test_create_weight_based_shipping_method(
        shipping_zone, staff_api_client, min_weight, max_weight,
        expected_min_weight, expected_max_weight, permission_manage_shipping):
    query = WEIGHT_BASED_SHIPPING_QUERY
    shipping_zone_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_zone.pk)
    variables = {
        'shippingZone': shipping_zone_id,
        'name': 'DHL',
        'price': 12.34,
        'minimumOrderWeight': min_weight,
        'maximumOrderWeight': max_weight,
        'type': ShippingMethodTypeEnum.WEIGHT.name}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)
    data = content['data']['shippingPriceCreate']
    assert data['shippingMethod']['minimumOrderWeight'] == expected_min_weight
    assert data['shippingMethod']['maximumOrderWeight'] == expected_max_weight
    assert data['shippingZone']['id'] == shipping_zone_id


def test_create_weight_shipping_method_errors(
        shipping_zone, staff_api_client, permission_manage_shipping):
    query = WEIGHT_BASED_SHIPPING_QUERY
    shipping_zone_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_zone.pk)
    variables = {
        'shippingZone': shipping_zone_id,
        'name': 'DHL',
        'price': 12.34,
        'minimumOrderWeight': 20,
        'maximumOrderWeight': 15,
        'type': ShippingMethodTypeEnum.WEIGHT.name}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)
    data = content['data']['shippingPriceCreate']
    assert (
        data['errors'][0]['message'] ==
        'Maximum order weight should be larger than the minimum order weight.')


def test_update_shipping_method(
        staff_api_client, shipping_zone, permission_manage_shipping):
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
            shippingZone {
                id
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
    price = 12.34
    assert not str(shipping_method.price) == price
    shipping_zone_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        'ShippingMethod', shipping_method.pk)
    variables = {
        'shippingZone': shipping_zone_id,
        'price': price,
        'id': shipping_method_id,
        'minimumOrderPrice': 12.00,
        'type': ShippingMethodTypeEnum.PRICE.name}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)
    data = content['data']['shippingPriceUpdate']
    assert data['shippingMethod']['price']['amount'] == float(price)
    assert data['shippingZone']['id'] == shipping_zone_id


def test_delete_shipping_method(
        staff_api_client, shipping_method, permission_manage_shipping):
    query = """
        mutation deleteShippingPrice($id: ID!) {
            shippingPriceDelete(id: $id) {
                shippingZone {
                    id
                }
                shippingMethod {
                    id
                }
            }
        }
        """
    shipping_method_id = graphene.Node.to_global_id(
        'ShippingMethod', shipping_method.pk)
    shipping_zone_id = graphene.Node.to_global_id(
        'ShippingZone', shipping_method.shipping_zone.pk)
    variables = {'id': shipping_method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)
    data = content['data']['shippingPriceDelete']
    assert data['shippingMethod']['id'] == shipping_method_id
    assert data['shippingZone']['id'] == shipping_zone_id
    with pytest.raises(shipping_method._meta.model.DoesNotExist):
        shipping_method.refresh_from_db()
