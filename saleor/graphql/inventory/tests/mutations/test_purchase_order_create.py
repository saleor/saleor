import graphene

from .....inventory import PurchaseOrderItemStatus
from .....inventory.error_codes import PurchaseOrderErrorCode
from .....inventory.models import PurchaseOrder, PurchaseOrderItem
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION_CREATE_PURCHASE_ORDER = """
mutation createPurchaseOrder($input: PurchaseOrderCreateInput!) {
    createPurchaseOrder(input: $input) {
        purchaseOrder {
            id
            supplierWarehouse {
                id
                name
            }
            channel {
                id
                slug
            }
            items {
                id
                productVariant {
                    id
                }
                quantityOrdered
                quantityReceived
                unitPrice {
                    amount
                    currency
                }
                countryOfOrigin
                status
            }
        }
        purchaseOrderErrors {
            field
            code
            message
            warehouses
            variants
        }
    }
}
"""


def test_create_purchase_order_success(
    staff_api_client,
    permission_manage_purchase_orders,
    variant,
    warehouse,
    supplier_warehouse,
    channel_USD,
):
    """Successfully create a purchase order with valid data."""
    # given
    variables = {
        "input": {
            "sourceWarehouseId": graphene.Node.to_global_id(
                "Warehouse", supplier_warehouse.id
            ),
            "destinationWarehouseId": graphene.Node.to_global_id(
                "Warehouse", warehouse.id
            ),
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
            "items": [
                {
                    "variantId": graphene.Node.to_global_id(
                        "ProductVariant", variant.id
                    ),
                    "quantityOrdered": 100,
                    "unitPriceAmount": "10.50",
                    "currency": "GBP",
                    "countryOfOrigin": "CN",
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PURCHASE_ORDER,
        variables=variables,
        permissions=[permission_manage_purchase_orders],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["createPurchaseOrder"]
    assert not data["purchaseOrderErrors"]
    assert PurchaseOrder.objects.count() == 1
    assert PurchaseOrderItem.objects.count() == 1

    po = PurchaseOrder.objects.first()
    assert po.source_warehouse == supplier_warehouse
    assert po.destination_warehouse == warehouse
    assert po.channel == channel_USD

    item = PurchaseOrderItem.objects.first()
    assert item.product_variant == variant
    assert item.quantity_ordered == 100
    assert item.quantity_received == 0
    assert item.unit_price_amount == 10.50
    assert item.total_price_amount == 1050.00  # 100 * 10.50
    assert item.currency == "GBP"
    assert item.country_of_origin == "CN"
    assert item.status == PurchaseOrderItemStatus.DRAFT


def test_create_purchase_order_source_warehouse_must_be_non_owned(
    staff_api_client, permission_manage_purchase_orders, variant, warehouse, channel_USD
):
    """Source warehouse must be a supplier (non-owned)."""
    # given - using owned warehouse as source (invalid)
    variables = {
        "input": {
            "sourceWarehouseId": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "destinationWarehouseId": graphene.Node.to_global_id(
                "Warehouse", warehouse.id
            ),
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
            "items": [
                {
                    "variantId": graphene.Node.to_global_id(
                        "ProductVariant", variant.id
                    ),
                    "quantityOrdered": 100,
                    "unitPriceAmount": "10.50",
                    "currency": "GBP",
                    "countryOfOrigin": "CN",
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PURCHASE_ORDER,
        variables=variables,
        permissions=[permission_manage_purchase_orders],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["createPurchaseOrder"]
    errors = data["purchaseOrderErrors"]
    assert len(errors) == 1
    assert errors[0]["code"] == PurchaseOrderErrorCode.WAREHOUSE_IS_OWNED.name
    assert errors[0]["field"] == "sourceWarehouseId"
    assert PurchaseOrder.objects.count() == 0


def test_create_purchase_order_destination_warehouse_must_be_owned(
    staff_api_client,
    permission_manage_purchase_orders,
    variant,
    supplier_warehouse,
    channel_USD,
):
    """Destination warehouse must be owned."""
    # given - using non-owned warehouse as destination (invalid)
    variables = {
        "input": {
            "sourceWarehouseId": graphene.Node.to_global_id(
                "Warehouse", supplier_warehouse.id
            ),
            "destinationWarehouseId": graphene.Node.to_global_id(
                "Warehouse", supplier_warehouse.id
            ),
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
            "items": [
                {
                    "variantId": graphene.Node.to_global_id(
                        "ProductVariant", variant.id
                    ),
                    "quantityOrdered": 100,
                    "unitPriceAmount": "10.50",
                    "currency": "GBP",
                    "countryOfOrigin": "CN",
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PURCHASE_ORDER,
        variables=variables,
        permissions=[permission_manage_purchase_orders],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["createPurchaseOrder"]
    errors = data["purchaseOrderErrors"]
    assert len(errors) == 1
    assert errors[0]["code"] == PurchaseOrderErrorCode.WAREHOUSE_NOT_OWNED.name
    assert errors[0]["field"] == "destinationWarehouseId"
    assert PurchaseOrder.objects.count() == 0


def test_create_purchase_order_without_items(
    staff_api_client,
    permission_manage_purchase_orders,
    warehouse,
    supplier_warehouse,
    channel_USD,
):
    """Draft purchase order can be created without items."""
    # given
    variables = {
        "input": {
            "sourceWarehouseId": graphene.Node.to_global_id(
                "Warehouse", supplier_warehouse.id
            ),
            "destinationWarehouseId": graphene.Node.to_global_id(
                "Warehouse", warehouse.id
            ),
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PURCHASE_ORDER,
        variables=variables,
        permissions=[permission_manage_purchase_orders],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["createPurchaseOrder"]
    assert not data["purchaseOrderErrors"]
    assert PurchaseOrder.objects.count() == 1
    assert PurchaseOrderItem.objects.count() == 0


def test_create_purchase_order_items_without_price(
    staff_api_client,
    permission_manage_purchase_orders,
    variant,
    warehouse,
    supplier_warehouse,
    channel_USD,
):
    """Items can be created without unit price or currency for draft POs."""
    # given
    variables = {
        "input": {
            "sourceWarehouseId": graphene.Node.to_global_id(
                "Warehouse", supplier_warehouse.id
            ),
            "destinationWarehouseId": graphene.Node.to_global_id(
                "Warehouse", warehouse.id
            ),
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
            "items": [
                {
                    "variantId": graphene.Node.to_global_id(
                        "ProductVariant", variant.id
                    ),
                    "quantityOrdered": 50,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PURCHASE_ORDER,
        variables=variables,
        permissions=[permission_manage_purchase_orders],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["createPurchaseOrder"]
    assert not data["purchaseOrderErrors"]
    assert PurchaseOrder.objects.count() == 1

    item = PurchaseOrderItem.objects.first()
    assert item.quantity_ordered == 50
    assert item.total_price_amount is None
    assert item.currency is None


def test_create_purchase_order_quantity_must_be_positive(
    staff_api_client,
    permission_manage_purchase_orders,
    variant,
    warehouse,
    supplier_warehouse,
    channel_USD,
):
    """Quantity must be greater than 0."""
    # given
    variables = {
        "input": {
            "sourceWarehouseId": graphene.Node.to_global_id(
                "Warehouse", supplier_warehouse.id
            ),
            "destinationWarehouseId": graphene.Node.to_global_id(
                "Warehouse", warehouse.id
            ),
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
            "items": [
                {
                    "variantId": graphene.Node.to_global_id(
                        "ProductVariant", variant.id
                    ),
                    "quantityOrdered": 0,
                    "unitPriceAmount": "10.50",
                    "currency": "GBP",
                    "countryOfOrigin": "CN",
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PURCHASE_ORDER,
        variables=variables,
        permissions=[permission_manage_purchase_orders],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["createPurchaseOrder"]
    errors = data["purchaseOrderErrors"]
    assert any(
        error["code"] == PurchaseOrderErrorCode.INVALID_QUANTITY.name
        for error in errors
    )
    assert PurchaseOrder.objects.count() == 0


def test_create_purchase_order_invalid_variant_id(
    staff_api_client,
    permission_manage_purchase_orders,
    warehouse,
    supplier_warehouse,
    channel_USD,
):
    """Invalid variant IDs should be rejected."""
    # given
    invalid_variant_id = graphene.Node.to_global_id("ProductVariant", 999999)
    variables = {
        "input": {
            "sourceWarehouseId": graphene.Node.to_global_id(
                "Warehouse", supplier_warehouse.id
            ),
            "destinationWarehouseId": graphene.Node.to_global_id(
                "Warehouse", warehouse.id
            ),
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
            "items": [
                {
                    "variantId": invalid_variant_id,
                    "quantityOrdered": 100,
                    "unitPriceAmount": "10.50",
                    "currency": "GBP",
                    "countryOfOrigin": "CN",
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PURCHASE_ORDER,
        variables=variables,
        permissions=[permission_manage_purchase_orders],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["createPurchaseOrder"]
    errors = data["purchaseOrderErrors"]
    assert any(
        error["code"] == PurchaseOrderErrorCode.INVALID_VARIANT.name for error in errors
    )
    assert PurchaseOrder.objects.count() == 0


def test_create_purchase_order_invalid_country_code(
    staff_api_client,
    permission_manage_purchase_orders,
    variant,
    warehouse,
    supplier_warehouse,
    channel_USD,
):
    """Invalid country codes should be rejected."""
    # given
    variables = {
        "input": {
            "sourceWarehouseId": graphene.Node.to_global_id(
                "Warehouse", supplier_warehouse.id
            ),
            "destinationWarehouseId": graphene.Node.to_global_id(
                "Warehouse", warehouse.id
            ),
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
            "items": [
                {
                    "variantId": graphene.Node.to_global_id(
                        "ProductVariant", variant.id
                    ),
                    "quantityOrdered": 100,
                    "unitPriceAmount": "10.50",
                    "currency": "GBP",
                    "countryOfOrigin": "XX",  # Invalid country code
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PURCHASE_ORDER,
        variables=variables,
        permissions=[permission_manage_purchase_orders],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["createPurchaseOrder"]
    errors = data["purchaseOrderErrors"]
    assert any(
        error["code"] == PurchaseOrderErrorCode.INVALID_COUNTRY.name for error in errors
    )
    assert PurchaseOrder.objects.count() == 0


def test_create_purchase_order_requires_permission(
    staff_api_client, variant, warehouse, supplier_warehouse, channel_USD
):
    """Permission is required to create purchase orders."""
    # given
    variables = {
        "input": {
            "sourceWarehouseId": graphene.Node.to_global_id(
                "Warehouse", supplier_warehouse.id
            ),
            "destinationWarehouseId": graphene.Node.to_global_id(
                "Warehouse", warehouse.id
            ),
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
            "items": [
                {
                    "variantId": graphene.Node.to_global_id(
                        "ProductVariant", variant.id
                    ),
                    "quantityOrdered": 100,
                    "unitPriceAmount": "10.50",
                    "currency": "GBP",
                    "countryOfOrigin": "CN",
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PURCHASE_ORDER, variables=variables, permissions=[]
    )

    # then
    assert_no_permission(response)
    assert PurchaseOrder.objects.count() == 0


def test_create_purchase_order_initial_status_is_draft(
    staff_api_client,
    permission_manage_purchase_orders,
    variant,
    warehouse,
    supplier_warehouse,
    channel_USD,
):
    """Verify initial status is DRAFT."""
    # given
    variables = {
        "input": {
            "sourceWarehouseId": graphene.Node.to_global_id(
                "Warehouse", supplier_warehouse.id
            ),
            "destinationWarehouseId": graphene.Node.to_global_id(
                "Warehouse", warehouse.id
            ),
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
            "items": [
                {
                    "variantId": graphene.Node.to_global_id(
                        "ProductVariant", variant.id
                    ),
                    "quantityOrdered": 100,
                    "unitPriceAmount": "10.50",
                    "currency": "GBP",
                    "countryOfOrigin": "CN",
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PURCHASE_ORDER,
        variables=variables,
        permissions=[permission_manage_purchase_orders],
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["createPurchaseOrder"]["purchaseOrderErrors"]

    item = PurchaseOrderItem.objects.first()
    assert item.status == PurchaseOrderItemStatus.DRAFT


def test_create_purchase_order_quantity_received_starts_at_zero(
    staff_api_client,
    permission_manage_purchase_orders,
    variant,
    warehouse,
    supplier_warehouse,
    channel_USD,
):
    """Verify quantity_received starts at 0."""
    # given
    variables = {
        "input": {
            "sourceWarehouseId": graphene.Node.to_global_id(
                "Warehouse", supplier_warehouse.id
            ),
            "destinationWarehouseId": graphene.Node.to_global_id(
                "Warehouse", warehouse.id
            ),
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
            "items": [
                {
                    "variantId": graphene.Node.to_global_id(
                        "ProductVariant", variant.id
                    ),
                    "quantityOrdered": 100,
                    "unitPriceAmount": "10.50",
                    "currency": "GBP",
                    "countryOfOrigin": "CN",
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PURCHASE_ORDER,
        variables=variables,
        permissions=[permission_manage_purchase_orders],
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["createPurchaseOrder"]["purchaseOrderErrors"]

    item = PurchaseOrderItem.objects.first()
    assert item.quantity_received == 0
