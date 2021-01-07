import graphene
import pytest
from measurement.measures import Weight

from ....core.weight import WeightUnits
from ....shipping.error_codes import ShippingErrorCode
from ....shipping.utils import get_countries_without_shipping_zone
from ...core.enums import WeightUnitsEnum
from ...shipping.resolvers import resolve_price_range
from ...tests.utils import get_graphql_content
from ..types import ShippingMethodTypeEnum

SHIPPING_ZONE_QUERY = """
    query ShippingQuery($id: ID!, $channel: String,) {
        shippingZone(id: $id, channel:$channel) {
            name
            shippingMethods {
                zipCodeRules {
                    start
                    end
                }
                channelListings {
                    id
                    price {
                        amount
                    }
                    maximumOrderPrice {
                        amount
                    }
                    minimumOrderPrice {
                        amount
                    }
                }
                minimumOrderWeight {
                    value
                    unit
                }
                maximumOrderWeight {
                    value
                    unit
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


def test_shipping_zone_query(
    staff_api_client, shipping_zone, permission_manage_shipping, channel_USD
):
    # given
    shipping = shipping_zone
    method = shipping.shipping_methods.first()
    code = method.zip_code_rules.create(start="HB2", end="HB6")
    query = SHIPPING_ZONE_QUERY
    ID = graphene.Node.to_global_id("ShippingZone", shipping.id)
    variables = {"id": ID, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )

    # then
    content = get_graphql_content(response)
    shipping_data = content["data"]["shippingZone"]
    assert shipping_data["name"] == shipping.name
    num_of_shipping_methods = shipping_zone.shipping_methods.count()
    assert len(shipping_data["shippingMethods"]) == num_of_shipping_methods
    assert shipping_data["shippingMethods"][0]["zipCodeRules"] == [
        {"start": code.start, "end": code.end}
    ]
    price_range = resolve_price_range(channel_slug=channel_USD.slug)
    data_price_range = shipping_data["priceRange"]
    assert data_price_range["start"]["amount"] == price_range.start.amount
    assert data_price_range["stop"]["amount"] == price_range.stop.amount


def test_shipping_zone_query_weights_returned_in_default_unit(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
    site_settings,
    channel_USD,
):
    # given
    shipping = shipping_zone
    shipping_method = shipping.shipping_methods.first()
    shipping_method.minimum_order_weight = Weight(kg=1)
    shipping_method.maximum_order_weight = Weight(kg=10)
    shipping_method.save(update_fields=["minimum_order_weight", "maximum_order_weight"])

    site_settings.default_weight_unit = WeightUnits.GRAM
    site_settings.save(update_fields=["default_weight_unit"])

    query = SHIPPING_ZONE_QUERY
    ID = graphene.Node.to_global_id("ShippingZone", shipping.id)
    variables = {"id": ID, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )

    # then
    content = get_graphql_content(response)

    shipping_data = content["data"]["shippingZone"]
    assert shipping_data["name"] == shipping.name
    num_of_shipping_methods = shipping_zone.shipping_methods.count()
    assert len(shipping_data["shippingMethods"]) == num_of_shipping_methods
    price_range = resolve_price_range(channel_slug=channel_USD.slug)
    data_price_range = shipping_data["priceRange"]
    assert data_price_range["start"]["amount"] == price_range.start.amount
    assert data_price_range["stop"]["amount"] == price_range.stop.amount
    assert shipping_data["shippingMethods"][0]["minimumOrderWeight"]["value"] == 1000
    assert (
        shipping_data["shippingMethods"][0]["minimumOrderWeight"]["unit"]
        == WeightUnits.GRAM.upper()
    )
    assert shipping_data["shippingMethods"][0]["maximumOrderWeight"]["value"] == 10000
    assert (
        shipping_data["shippingMethods"][0]["maximumOrderWeight"]["unit"]
        == WeightUnits.GRAM.upper()
    )


def test_shipping_zones_query(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
    permission_manage_products,
    channel_USD,
):
    query = """
    query MultipleShippings($channel: String) {
        shippingZones(first: 100, channel: $channel) {
            edges {
                node {
                    id
                    name
                    priceRange {
                        start {
                            amount
                        }
                        stop {
                            amount
                        }
                    }
                    shippingMethods {
                        channelListings {
                            price {
                                amount
                            }
                        }
                    }
                    warehouses {
                        id
                        name
                    }
                }
            }
            totalCount
        }
    }
    """
    num_of_shippings = shipping_zone._meta.model.objects.count()
    variables = {"channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_shipping, permission_manage_products],
    )
    content = get_graphql_content(response)
    assert content["data"]["shippingZones"]["totalCount"] == num_of_shippings


def test_shipping_methods_query_with_channel(
    staff_api_client,
    shipping_zone,
    shipping_method_channel_PLN,
    permission_manage_shipping,
    permission_manage_products,
    channel_USD,
):
    query = """
    query MultipleShippings($channel: String) {
        shippingZones(first: 100, channel: $channel) {
            edges {
                node {
                    shippingMethods {
                        channelListings {
                            price {
                                amount
                            }
                        }
                    }
                }
            }
        }
    }
    """
    shipping_zone.shipping_methods.add(shipping_method_channel_PLN)
    variables = {"channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_shipping, permission_manage_products],
    )
    content = get_graphql_content(response)
    assert (
        len(content["data"]["shippingZones"]["edges"][0]["node"]["shippingMethods"])
        == 1
    )


def test_shipping_methods_query(
    staff_api_client,
    shipping_zone,
    shipping_method_channel_PLN,
    permission_manage_shipping,
    permission_manage_products,
    channel_USD,
):
    query = """
    query MultipleShippings {
        shippingZones(first: 100) {
            edges {
                node {
                    shippingMethods {
                        channelListings {
                            price {
                                amount
                            }
                        }
                    }
                }
            }
        }
    }
    """
    shipping_zone.shipping_methods.add(shipping_method_channel_PLN)
    response = staff_api_client.post_graphql(
        query,
        permissions=[permission_manage_shipping, permission_manage_products],
    )
    content = get_graphql_content(response)
    assert (
        len(content["data"]["shippingZones"]["edges"][0]["node"]["shippingMethods"])
        == 2
    )


CREATE_SHIPPING_ZONE_QUERY = """
    mutation createShipping(
        $name: String
        $description: String
        $default: Boolean
        $countries: [String]
        $addWarehouses: [ID]
    ) {
        shippingZoneCreate(
            input: {
                name: $name
                description: $description
                countries: $countries
                default: $default
                addWarehouses: $addWarehouses
            }
        ) {
            shippingErrors {
                field
                code
            }
            shippingZone {
                name
                description
                countries {
                    code
                }
                default
                warehouses {
                    name
                }
            }
        }
    }
"""


def test_create_shipping_zone(staff_api_client, warehouse, permission_manage_shipping):
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "name": "test shipping",
        "description": "test description",
        "countries": ["PL"],
        "addWarehouses": [warehouse_id],
    }
    response = staff_api_client.post_graphql(
        CREATE_SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneCreate"]
    zone = data["shippingZone"]
    assert zone["name"] == "test shipping"
    assert zone["description"] == "test description"
    assert zone["countries"] == [{"code": "PL"}]
    assert zone["warehouses"][0]["name"] == warehouse.name
    assert zone["default"] is False


def test_create_shipping_zone_with_empty_warehouses(
    staff_api_client, permission_manage_shipping
):
    variables = {
        "name": "test shipping",
        "countries": ["PL"],
        "addWarehouses": [],
    }
    response = staff_api_client.post_graphql(
        CREATE_SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneCreate"]
    assert not data["shippingErrors"]
    zone = data["shippingZone"]
    assert zone["name"] == "test shipping"
    assert zone["countries"] == [{"code": "PL"}]
    assert not zone["warehouses"]
    assert zone["default"] is False


def test_create_shipping_zone_without_warehouses(
    staff_api_client, permission_manage_shipping
):
    variables = {
        "name": "test shipping",
        "countries": ["PL"],
    }
    response = staff_api_client.post_graphql(
        CREATE_SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneCreate"]
    assert not data["shippingErrors"]
    zone = data["shippingZone"]
    assert zone["name"] == "test shipping"
    assert zone["countries"] == [{"code": "PL"}]
    assert not zone["warehouses"]
    assert zone["default"] is False


def test_create_default_shipping_zone(
    staff_api_client, warehouse, permission_manage_shipping
):
    unassigned_countries = set(get_countries_without_shipping_zone())
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "default": True,
        "name": "test shipping",
        "countries": ["PL"],
        "addWarehouses": [warehouse_id],
    }
    response = staff_api_client.post_graphql(
        CREATE_SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneCreate"]
    assert not data["shippingErrors"]
    zone = data["shippingZone"]
    assert zone["name"] == "test shipping"
    assert zone["warehouses"][0]["name"] == warehouse.name
    assert zone["default"] is True
    zone_countries = {c.code for c in zone["countries"]}
    assert zone_countries == unassigned_countries


def test_create_duplicated_default_shipping_zone(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    shipping_zone.default = True
    shipping_zone.save()

    variables = {"default": True, "name": "test shipping", "countries": ["PL"]}
    response = staff_api_client.post_graphql(
        CREATE_SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneCreate"]
    assert data["shippingErrors"]
    assert data["shippingErrors"][0]["field"] == "default"
    assert data["shippingErrors"][0]["code"] == ShippingErrorCode.ALREADY_EXISTS.name


CREATE_SHIPPING_METHOD_ZIP_CODE_MUTATION = """
    mutation createZipCode(
        $shippingMethodId: ID!, $zipCodeRules: [ShippingZipCodeRulesCreateInputRange]!
    ){
        shippingMethodZipCodeRulesCreate(
            shippingMethodId: $shippingMethodId
            input: {
                zipCodeRules: $zipCodeRules
            }
        ){
            zipCodeRules {
                start
                end
            }
            shippingMethod {
                id
                name
            }
            shippingErrors {
                field
                code
            }
        }
    }
"""


def test_create_shipping_method_zip_code(
    staff_api_client, shipping_method, permission_manage_shipping
):
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    zip_code_rules = [
        {"start": "HB3", "end": "HB6"},
        {"start": "HB8", "end": None},
    ]
    variables = {"shippingMethodId": shipping_method_id, "zipCodeRules": zip_code_rules}
    response = staff_api_client.post_graphql(
        CREATE_SHIPPING_METHOD_ZIP_CODE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    assert not content["data"]["shippingMethodZipCodeRulesCreate"]["shippingErrors"]
    zip_code_rules_data = content["data"]["shippingMethodZipCodeRulesCreate"][
        "zipCodeRules"
    ]
    shipping_method_data = content["data"]["shippingMethodZipCodeRulesCreate"][
        "shippingMethod"
    ]
    assert shipping_method_data["id"] == shipping_method_id
    assert shipping_method_data["name"] == shipping_method.name
    assert zip_code_rules_data == zip_code_rules


def test_create_shipping_method_zip_code_duplicate_entry(
    staff_api_client, shipping_method, permission_manage_shipping
):
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    zip_code_rules = [
        {"start": "HB3", "end": "HB6"},
        {"start": "HB3", "end": "HB6"},
    ]
    variables = {"shippingMethodId": shipping_method_id, "zipCodeRules": zip_code_rules}
    response = staff_api_client.post_graphql(
        CREATE_SHIPPING_METHOD_ZIP_CODE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    errors = content["data"]["shippingMethodZipCodeRulesCreate"]["shippingErrors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.ALREADY_EXISTS.name
    assert errors[0]["field"] == "zipCodeRules"


DELETE_SHIPPING_METHOD_ZIP_CODE_MUTATION = """
    mutation deleteZipCode(
        $id: ID!
    ){
        shippingMethodZipCodeRulesDelete(
            id: $id
        ){
            shippingMethod {
                id
                name
            }
            shippingErrors {
                field
                code
            }
        }
    }
"""


def test_delete_shipping_method_zip_code(
    staff_api_client, shipping_method_excldued_by_zip_code, permission_manage_shipping
):
    shipping_zip_code_id = graphene.Node.to_global_id(
        "ShippingMethodZipCodeRule",
        shipping_method_excldued_by_zip_code.zip_code_rules.first().id,
    )
    response = staff_api_client.post_graphql(
        DELETE_SHIPPING_METHOD_ZIP_CODE_MUTATION,
        {"id": shipping_zip_code_id},
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingMethodZipCodeRulesDelete"]
    assert data["shippingErrors"] == []
    assert data["shippingMethod"]["id"] == graphene.Node.to_global_id(
        "ShippingMethod", shipping_method_excldued_by_zip_code.id
    )
    assert data["shippingMethod"]["name"] == shipping_method_excldued_by_zip_code.name
    assert not shipping_method_excldued_by_zip_code.zip_code_rules.exists()


UPDATE_SHIPPING_ZONE_QUERY = """
    mutation updateShipping(
        $id: ID!
        $name: String
        $description: String
        $default: Boolean
        $countries: [String]
        $addWarehouses: [ID]
        $removeWarehouses: [ID]
    ) {
        shippingZoneUpdate(
            id: $id
            input: {
                name: $name
                description: $description
                default: $default
                countries: $countries
                addWarehouses: $addWarehouses
                removeWarehouses: $removeWarehouses
            }
        ) {
            shippingZone {
                name
                description
                warehouses {
                    name
                    slug
                }
            }
            shippingErrors {
                field
                code
                warehouses
            }
        }
    }
"""


def test_update_shipping_zone(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    name = "Parabolic name"
    description = "Description of a shipping zone."
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {
        "id": shipping_id,
        "name": name,
        "countries": [],
        "description": description,
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["shippingErrors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    assert data["name"] == name
    assert data["description"] == description


def test_update_shipping_zone_default_exists(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    default_zone = shipping_zone
    default_zone.default = True
    default_zone.pk = None
    default_zone.save()
    shipping_zone = shipping_zone.__class__.objects.filter(default=False).get()

    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {"id": shipping_id, "name": "Name", "countries": [], "default": True}
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert data["shippingErrors"][0]["field"] == "default"
    assert data["shippingErrors"][0]["code"] == ShippingErrorCode.ALREADY_EXISTS.name


def test_update_shipping_zone_add_warehouses(
    staff_api_client,
    shipping_zone,
    warehouses,
    permission_manage_shipping,
):
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", warehouse.pk)
        for warehouse in warehouses
    ]
    warehouse_names = [warehouse.name for warehouse in warehouses]

    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "addWarehouses": warehouse_ids,
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["shippingErrors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    for response_warehouse in data["warehouses"]:
        assert response_warehouse["name"] in warehouse_names
    assert len(data["warehouses"]) == len(warehouse_names)


def test_update_shipping_zone_add_second_warehouses(
    staff_api_client,
    shipping_zone,
    warehouse,
    warehouse_no_shipping_zone,
    permission_manage_shipping,
):
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    warehouse_id = graphene.Node.to_global_id(
        "Warehouse", warehouse_no_shipping_zone.pk
    )
    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "addWarehouses": [warehouse_id],
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["shippingErrors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    assert data["warehouses"][1]["slug"] == warehouse.slug
    assert data["warehouses"][0]["slug"] == warehouse_no_shipping_zone.slug


def test_update_shipping_zone_remove_warehouses(
    staff_api_client,
    shipping_zone,
    warehouse,
    permission_manage_shipping,
):
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "removeWarehouses": [warehouse_id],
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["shippingErrors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    assert not data["warehouses"]


def test_update_shipping_zone_remove_one_warehouses(
    staff_api_client,
    shipping_zone,
    warehouses,
    permission_manage_shipping,
):
    for warehouse in warehouses:
        warehouse.shipping_zones.add(shipping_zone)
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouses[0].pk)
    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "removeWarehouses": [warehouse_id],
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["shippingErrors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    assert data["warehouses"][0]["name"] == warehouses[1].name
    assert len(data["warehouses"]) == 1


def test_update_shipping_zone_replace_warehouse(
    staff_api_client,
    shipping_zone,
    warehouse,
    warehouse_no_shipping_zone,
    permission_manage_shipping,
):
    assert shipping_zone.warehouses.first() == warehouse

    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    add_warehouse_id = graphene.Node.to_global_id(
        "Warehouse", warehouse_no_shipping_zone.pk
    )
    remove_warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "addWarehouses": [add_warehouse_id],
        "removeWarehouses": [remove_warehouse_id],
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert not data["shippingErrors"]
    data = content["data"]["shippingZoneUpdate"]["shippingZone"]
    assert data["warehouses"][0]["name"] == warehouse_no_shipping_zone.name
    assert len(data["warehouses"]) == 1


def test_update_shipping_zone_same_warehouse_id_in_add_and_remove(
    staff_api_client,
    shipping_zone,
    warehouse,
    permission_manage_shipping,
):
    shipping_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    variables = {
        "id": shipping_id,
        "name": shipping_zone.name,
        "addWarehouses": [warehouse_id],
        "removeWarehouses": [warehouse_id],
    }
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_ZONE_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneUpdate"]
    assert data["shippingErrors"]
    assert data["shippingErrors"][0]["field"] == "removeWarehouses"
    assert (
        data["shippingErrors"][0]["code"]
        == ShippingErrorCode.DUPLICATED_INPUT_ITEM.name
    )
    assert data["shippingErrors"][0]["warehouses"][0] == warehouse_id


def test_delete_shipping_zone(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = """
        mutation deleteShippingZone($id: ID!) {
            shippingZoneDelete(id: $id) {
                shippingZone {
                    name
                }
            }
        }
    """
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {"id": shipping_zone_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingZoneDelete"]["shippingZone"]
    assert data["name"] == shipping_zone.name
    with pytest.raises(shipping_zone._meta.model.DoesNotExist):
        shipping_zone.refresh_from_db()


PRICE_BASED_SHIPPING_QUERY = """
    mutation createShippingPrice(
        $type: ShippingMethodTypeEnum,
        $name: String!,
        $shippingZone: ID!,
        $maximumDeliveryDays: Int,
        $minimumDeliveryDays: Int,
    ) {
    shippingPriceCreate(
        input: {
            name: $name, shippingZone: $shippingZone, type: $type,
            maximumDeliveryDays: $maximumDeliveryDays,
            minimumDeliveryDays: $minimumDeliveryDays,
        }) {
        shippingErrors {
            field
            code
        }
        shippingZone {
            id
        }
        shippingMethod {
            id
            name
            channelListings {
            price {
                amount
            }
            minimumOrderPrice {
                amount
            }
            maximumOrderPrice {
                amount
            }
            }
            type
            minimumDeliveryDays
            maximumDeliveryDays
            }
        }
    }
"""


@pytest.mark.parametrize(
    "min_price, max_price, expected_min_price, expected_max_price",
    (
        (10.32, 15.43, {"amount": 10.32}, {"amount": 15.43}),
        (10.33, None, {"amount": 10.33}, None),
    ),
)
def test_create_shipping_method(
    staff_api_client,
    shipping_zone,
    min_price,
    max_price,
    expected_min_price,
    expected_max_price,
    permission_manage_shipping,
):
    name = "DHL"
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    max_del_days = 10
    min_del_days = 3
    variables = {
        "shippingZone": shipping_zone_id,
        "name": name,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
    }
    response = staff_api_client.post_graphql(
        PRICE_BASED_SHIPPING_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    errors = data["shippingErrors"]
    assert not errors
    assert data["shippingMethod"]["name"] == name
    assert data["shippingMethod"]["type"] == ShippingMethodTypeEnum.PRICE.name
    assert data["shippingZone"]["id"] == shipping_zone_id
    assert data["shippingMethod"]["minimumDeliveryDays"] == min_del_days
    assert data["shippingMethod"]["maximumDeliveryDays"] == max_del_days


def test_create_shipping_method_minimum_delivery_days_higher_than_maximum(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
):
    name = "DHL"
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    max_del_days = 3
    min_del_days = 10
    variables = {
        "shippingZone": shipping_zone_id,
        "name": name,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
    }
    response = staff_api_client.post_graphql(
        PRICE_BASED_SHIPPING_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    errors = data["shippingErrors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "minimumDeliveryDays"


def test_create_shipping_method_minimum_delivery_days_below_0(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
):
    name = "DHL"
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    max_del_days = 3
    min_del_days = -1
    variables = {
        "shippingZone": shipping_zone_id,
        "name": name,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
    }
    response = staff_api_client.post_graphql(
        PRICE_BASED_SHIPPING_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    errors = data["shippingErrors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "minimumDeliveryDays"


def test_create_shipping_method_maximum_delivery_days_below_0(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
):
    name = "DHL"
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    max_del_days = -1
    min_del_days = 10
    variables = {
        "shippingZone": shipping_zone_id,
        "name": name,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
    }
    response = staff_api_client.post_graphql(
        PRICE_BASED_SHIPPING_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    errors = data["shippingErrors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "maximumDeliveryDays"


WEIGHT_BASED_SHIPPING_QUERY = """
    mutation createShippingPrice(
        $type: ShippingMethodTypeEnum, $name: String!,
        $shippingZone: ID!, $maximumOrderWeight: WeightScalar,
        $minimumOrderWeight: WeightScalar) {
        shippingPriceCreate(
            input: {
                name: $name,shippingZone: $shippingZone,
                minimumOrderWeight:$minimumOrderWeight,
                maximumOrderWeight: $maximumOrderWeight, type: $type}) {
            shippingErrors {
                field
                code
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
    "min_weight, max_weight, expected_min_weight, expected_max_weight",
    (
        (
            10.32,
            15.64,
            {"value": 10.32, "unit": WeightUnitsEnum.KG.name},
            {"value": 15.64, "unit": WeightUnitsEnum.KG.name},
        ),
        (10.92, None, {"value": 10.92, "unit": WeightUnitsEnum.KG.name}, None),
    ),
)
def test_create_weight_based_shipping_method(
    shipping_zone,
    staff_api_client,
    min_weight,
    max_weight,
    expected_min_weight,
    expected_max_weight,
    permission_manage_shipping,
):
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {
        "shippingZone": shipping_zone_id,
        "name": "DHL",
        "minimumOrderWeight": min_weight,
        "maximumOrderWeight": max_weight,
        "type": ShippingMethodTypeEnum.WEIGHT.name,
    }
    response = staff_api_client.post_graphql(
        WEIGHT_BASED_SHIPPING_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    assert data["shippingMethod"]["minimumOrderWeight"] == expected_min_weight
    assert data["shippingMethod"]["maximumOrderWeight"] == expected_max_weight
    assert data["shippingZone"]["id"] == shipping_zone_id


def test_create_weight_shipping_method_errors(
    shipping_zone, staff_api_client, permission_manage_shipping
):
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {
        "shippingZone": shipping_zone_id,
        "name": "DHL",
        "minimumOrderWeight": 20,
        "maximumOrderWeight": 15,
        "type": ShippingMethodTypeEnum.WEIGHT.name,
    }
    response = staff_api_client.post_graphql(
        WEIGHT_BASED_SHIPPING_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    assert data["shippingErrors"][0]["code"] == ShippingErrorCode.MAX_LESS_THAN_MIN.name


def test_create_shipping_method_with_negative_min_weight(
    shipping_zone, staff_api_client, permission_manage_shipping
):
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {
        "shippingZone": shipping_zone_id,
        "name": "DHL",
        "minimumOrderWeight": -20,
        "type": ShippingMethodTypeEnum.WEIGHT.name,
    }
    response = staff_api_client.post_graphql(
        WEIGHT_BASED_SHIPPING_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    error = data["shippingErrors"][0]
    assert error["field"] == "minimumOrderWeight"
    assert error["code"] == ShippingErrorCode.INVALID.name


def test_create_shipping_method_with_negative_max_weight(
    shipping_zone, staff_api_client, permission_manage_shipping
):
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {
        "shippingZone": shipping_zone_id,
        "name": "DHL",
        "maximumOrderWeight": -15,
        "type": ShippingMethodTypeEnum.WEIGHT.name,
    }
    response = staff_api_client.post_graphql(
        WEIGHT_BASED_SHIPPING_QUERY, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    error = data["shippingErrors"][0]
    assert error["field"] == "maximumOrderWeight"
    assert error["code"] == ShippingErrorCode.INVALID.name


UPDATE_SHIPPING_PRICE_MUTATION = """
    mutation updateShippingPrice(
        $id: ID!,
        $shippingZone: ID!,
        $type: ShippingMethodTypeEnum!,
        $maximumDeliveryDays: Int,
        $minimumDeliveryDays: Int,
        $maximumOrderWeight: WeightScalar,
        $minimumOrderWeight: WeightScalar,
    ) {
        shippingPriceUpdate(
            id: $id, input: {
                shippingZone: $shippingZone,
                type: $type,
                maximumDeliveryDays: $maximumDeliveryDays,
                minimumDeliveryDays: $minimumDeliveryDays,
                minimumOrderWeight:$minimumOrderWeight,
                maximumOrderWeight: $maximumOrderWeight,
            }) {
            shippingErrors {
                field
                code
            }
            shippingZone {
                id
            }
            shippingMethod {
                type
                minimumDeliveryDays
                maximumDeliveryDays
            }
        }
    }
"""


def test_update_shipping_method(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    max_del_days = 8
    min_del_days = 2
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    assert data["shippingZone"]["id"] == shipping_zone_id
    assert data["shippingMethod"]["minimumDeliveryDays"] == min_del_days
    assert data["shippingMethod"]["maximumDeliveryDays"] == max_del_days


def test_update_shipping_method_minimum_delivery_days_higher_than_maximum(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    max_del_days = 2
    min_del_days = 8
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    errors = data["shippingErrors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "minimumDeliveryDays"


def test_update_shipping_method_minimum_delivery_days_below_0(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    max_del_days = 2
    min_del_days = -1
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    errors = data["shippingErrors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "minimumDeliveryDays"


def test_update_shipping_method_maximum_delivery_days_below_0(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    max_del_days = -1
    min_del_days = 10
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    errors = data["shippingErrors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "maximumDeliveryDays"


def test_update_shipping_method_minimum_delivery_days_higher_than_max_from_instance(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_method.maximum_delivery_days = 5
    shipping_method.save(update_fields=["maximum_delivery_days"])
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    min_del_days = 8
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "minimumDeliveryDays": min_del_days,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    errors = data["shippingErrors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "minimumDeliveryDays"


def test_update_shipping_method_maximum_delivery_days_lower_than_min_from_instance(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_method.minimum_delivery_days = 10
    shipping_method.save(update_fields=["minimum_delivery_days"])
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    max_del_days = 5
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    errors = data["shippingErrors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "maximumDeliveryDays"


def test_update_shipping_method_multiple_errors(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_method.minimum_delivery_days = 10
    shipping_method.save(update_fields=["minimum_delivery_days"])
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    max_del_days = 5
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumOrderWeight": {"value": -2, "unit": WeightUnitsEnum.KG.name},
        "maximumOrderWeight": {"value": -1, "unit": WeightUnitsEnum.KG.name},
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    errors = data["shippingErrors"]
    assert not data["shippingMethod"]
    assert len(errors) == 3
    expected_errors = [
        {"code": ShippingErrorCode.INVALID.name, "field": "maximumDeliveryDays"},
        {"code": ShippingErrorCode.INVALID.name, "field": "minimumOrderWeight"},
        {"code": ShippingErrorCode.INVALID.name, "field": "maximumOrderWeight"},
    ]
    for error in expected_errors:
        assert error in errors


@pytest.mark.parametrize(
    "min_delivery_days, max_delivery_days",
    [
        (None, 1),
        (1, None),
        (None, None),
    ],
)
def test_update_shipping_method_delivery_days_without_value(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
    min_delivery_days,
    max_delivery_days,
):
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "minimumDeliveryDays": min_delivery_days,
        "maximumDeliveryDays": max_delivery_days,
    }

    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_PRICE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    shipping_method.refresh_from_db()

    assert not content["data"]["shippingPriceUpdate"]["shippingErrors"]
    assert shipping_method.minimum_delivery_days == min_delivery_days
    assert shipping_method.maximum_delivery_days == max_delivery_days


def test_delete_shipping_method(
    staff_api_client, shipping_method, permission_manage_shipping
):
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
        "ShippingMethod", shipping_method.pk
    )
    shipping_zone_id = graphene.Node.to_global_id(
        "ShippingZone", shipping_method.shipping_zone.pk
    )
    variables = {"id": shipping_method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceDelete"]
    assert data["shippingMethod"]["id"] == shipping_method_id
    assert data["shippingZone"]["id"] == shipping_zone_id
    with pytest.raises(shipping_method._meta.model.DoesNotExist):
        shipping_method.refresh_from_db()


EXCLUDE_PRODUCTS_MUTATION = """
    mutation shippingPriceRemoveProductFromExclude(
        $id: ID!, $input:ShippingPriceExcludeProductsInput!
        ) {
        shippingPriceExcludeProducts(
            id: $id
            input: $input) {
            shippingErrors {
                field
                code
            }
            shippingMethod {
                id
                excludedProducts(first:10){
                   totalCount
                   edges{
                     node{
                       id
                     }
                   }
                }
            }
        }
    }
"""


@pytest.mark.parametrize("requestor", ["staff", "app"])
def test_exclude_products_for_shipping_method_only_products(
    requestor,
    app_api_client,
    shipping_method,
    product_list,
    staff_api_client,
    permission_manage_shipping,
):
    api = staff_api_client if requestor == "staff" else app_api_client
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    product_ids = [graphene.Node.to_global_id("Product", p.pk) for p in product_list]
    variables = {"id": shipping_method_id, "input": {"products": product_ids}}
    response = api.post_graphql(
        EXCLUDE_PRODUCTS_MUTATION, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    shipping_method = content["data"]["shippingPriceExcludeProducts"]["shippingMethod"]
    excluded_products = shipping_method["excludedProducts"]
    total_count = excluded_products["totalCount"]
    excluded_product_ids = {p["node"]["id"] for p in excluded_products["edges"]}
    assert len(product_ids) == total_count
    assert excluded_product_ids == set(product_ids)


@pytest.mark.parametrize("requestor", ["staff", "app"])
def test_exclude_products_for_shipping_method_already_has_excluded_products(
    requestor,
    shipping_method,
    product_list,
    product,
    staff_api_client,
    permission_manage_shipping,
    app_api_client,
):
    api = staff_api_client if requestor == "staff" else app_api_client
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    shipping_method.excluded_products.add(product, product_list[0])
    product_ids = [graphene.Node.to_global_id("Product", p.pk) for p in product_list]
    variables = {"id": shipping_method_id, "input": {"products": product_ids}}
    response = api.post_graphql(
        EXCLUDE_PRODUCTS_MUTATION, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    shipping_method = content["data"]["shippingPriceExcludeProducts"]["shippingMethod"]
    excluded_products = shipping_method["excludedProducts"]
    total_count = excluded_products["totalCount"]
    expected_product_ids = product_ids
    expected_product_ids.append(graphene.Node.to_global_id("Product", product.pk))
    excluded_product_ids = {p["node"]["id"] for p in excluded_products["edges"]}
    assert len(expected_product_ids) == total_count
    assert excluded_product_ids == set(expected_product_ids)


REMOVE_PRODUCTS_FROM_EXCLUDED_PRODUCTS_MUTATION = """
    mutation shippingPriceRemoveProductFromExclude(
        $id: ID!, $products: [ID]!
        ) {
        shippingPriceRemoveProductFromExclude(
            id: $id
            products: $products) {
            shippingErrors {
                field
                code
            }
            shippingMethod {
                id
                excludedProducts(first:10){
                   totalCount
                   edges{
                     node{
                       id
                     }
                   }
                }
            }
        }
    }
"""


@pytest.mark.parametrize("requestor", ["staff", "app"])
def test_remove_products_from_excluded_products_for_shipping_method_delete_all_products(
    requestor,
    shipping_method,
    product_list,
    staff_api_client,
    permission_manage_shipping,
    app_api_client,
):
    api = staff_api_client if requestor == "staff" else app_api_client
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    shipping_method.excluded_products.set(product_list)

    product_ids = [graphene.Node.to_global_id("Product", p.pk) for p in product_list]
    variables = {"id": shipping_method_id, "products": product_ids}
    response = api.post_graphql(
        REMOVE_PRODUCTS_FROM_EXCLUDED_PRODUCTS_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    content = get_graphql_content(response)
    shipping_method = content["data"]["shippingPriceRemoveProductFromExclude"][
        "shippingMethod"
    ]
    excluded_products = shipping_method["excludedProducts"]
    total_count = excluded_products["totalCount"]
    excluded_product_ids = {p["node"]["id"] for p in excluded_products["edges"]}
    assert total_count == 0
    assert len(excluded_product_ids) == 0


@pytest.mark.parametrize("requestor", ["staff", "app"])
def test_remove_products_from_excluded_products_for_shipping_method(
    requestor,
    shipping_method,
    product_list,
    staff_api_client,
    permission_manage_shipping,
    product,
    app_api_client,
):
    api = staff_api_client if requestor == "staff" else app_api_client
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    shipping_method.excluded_products.set(product_list)
    shipping_method.excluded_products.add(product)

    product_ids = [
        graphene.Node.to_global_id("Product", product.pk),
    ]
    variables = {"id": shipping_method_id, "products": product_ids}
    response = api.post_graphql(
        REMOVE_PRODUCTS_FROM_EXCLUDED_PRODUCTS_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    content = get_graphql_content(response)
    shipping_method = content["data"]["shippingPriceRemoveProductFromExclude"][
        "shippingMethod"
    ]
    excluded_products = shipping_method["excludedProducts"]
    total_count = excluded_products["totalCount"]
    expected_product_ids = {
        graphene.Node.to_global_id("Product", p.pk) for p in product_list
    }
    excluded_product_ids = {p["node"]["id"] for p in excluded_products["edges"]}
    assert total_count == len(expected_product_ids)
    assert excluded_product_ids == expected_product_ids
