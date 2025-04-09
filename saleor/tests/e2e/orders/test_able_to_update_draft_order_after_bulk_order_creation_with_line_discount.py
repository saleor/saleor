import graphene
from django.utils import timezone

from .. import DEFAULT_ADDRESS
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_shop
from ..taxes.utils import update_country_tax_rates
from ..utils import assert_address_data, assign_permissions
from .utils import draft_order_update, order_bulk_create, order_query


def prepare_order_bulk_create_input(
    customer_user,
    product_variant_id,
    warehouse_id,
    shipping_method_id,
    channel_slug,
    currency,
    tax_class_id,
    line_discount_data,
):
    user = {
        "id": graphene.Node.to_global_id("User", customer_user.id),
        "email": None,
    }
    delivery_method = {
        "shippingMethodId": shipping_method_id,
        "shippingMethodName": "Denormalized name",
        "shippingPrice": {
            "gross": 60,
            "net": 50,
        },
        "shippingTaxRate": 0.2,
        "shippingTaxClassId": tax_class_id,
        "shippingTaxClassName": "Denormalized name",
    }
    line = {
        "variantId": product_variant_id,
        "createdAt": timezone.now(),
        "productName": "Product Name",
        "variantName": "Variant Name",
        "translatedProductName": "Nazwa Produktu",
        "translatedVariantName": "Nazwa Wariantu",
        "isShippingRequired": True,
        "isGiftCard": False,
        "quantity": 5,
        "totalPrice": {
            "gross": 120,
            "net": 100,
        },
        "undiscountedTotalPrice": {
            "gross": 120,
            "net": 100,
        },
        "taxRate": 0.2,
        "taxClassId": tax_class_id,
        "warehouse": warehouse_id,
        "metadata": [{"key": "md key", "value": "md value"}],
        "privateMetadata": [{"key": "pmd key", "value": "pmd value"}],
        **line_discount_data,
    }
    return {
        "channel": channel_slug,
        "createdAt": timezone.now(),
        "status": "DRAFT",
        "user": user,
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
        "currency": currency,
        "languageCode": "PL",
        "deliveryMethod": delivery_method,
        "lines": [line],
        "weight": "10.15",
        "redirectUrl": "https://www.example.com",
        "metadata": [{"key": "md key", "value": "md value"}],
        "privateMetadata": [{"key": "pmd key", "value": "pmd value"}],
    }


def test_able_to_update_draft_order_after_bulk_order_creation_with_line_discount_CORE_0258(
    e2e_staff_api_client,
    e2e_logged_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_orders_import,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_orders_import,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shipping_country = "US"
    shipping_class_tax_rate = 8
    tax_settings = {
        "charge_taxes": True,
        "tax_calculation_strategy": "FLAT_RATES",
        "display_gross_prices": False,
        "prices_entered_with_tax": True,
        "tax_rates": [
            {
                "type": "shipping_country",
                "name": "Shipping Country Tax Rate",
                "country_code": shipping_country,
                "rate": shipping_class_tax_rate,
            },
        ],
    }
    price = 10

    shop_data, tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "shipping_methods": [
                            {
                                "add_channels": {},
                            },
                            {
                                "name": "Another shipping method",
                                "add_channels": {},
                            },
                        ],
                    },
                ],
                "order_settings": {},
            },
        ],
        tax_settings=tax_settings,
    )
    channel_data = shop_data[0]
    channel_id = channel_data["id"]
    channel_slug = channel_data["slug"]
    currency = channel_data["currency"]
    warehouse_id = channel_data["warehouse_id"]
    shipping_method_id = channel_data["shipping_zones"][0]["shipping_methods"][0]["id"]
    shipping_method_id_2 = channel_data["shipping_zones"][0]["shipping_methods"][1][
        "id"
    ]
    tax_class_id = tax_config[0]["shipping_country_tax_class_id"]

    update_country_tax_rates(
        e2e_staff_api_client,
        shipping_country,
        [{"rate": shipping_class_tax_rate}],
    )

    _product_id, product_variant_id, _product_variant_price = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        price,
    )

    line_discount_data = {
        "unitDiscountValue": 10,
        "unitDiscountType": "FIXED",
        "unitDiscountReason": "Test discount",
        "totalPrice": {
            "net": 50,
            "gross": 60,
        },
    }
    order_input = prepare_order_bulk_create_input(
        e2e_logged_api_client.user,
        product_variant_id,
        warehouse_id,
        shipping_method_id,
        channel_slug,
        currency,
        tax_class_id,
        line_discount_data,
    )

    # Step 1 - Create order with order bulk create
    create_order_response = order_bulk_create(e2e_staff_api_client, [order_input])

    assert create_order_response["count"] == 1

    draft_order = create_order_response["results"][0]["order"]
    assert draft_order
    order_id = draft_order["id"]
    assert len(draft_order["lines"]) == 1
    line = draft_order["lines"][0]
    assert line["unitDiscountValue"] == line_discount_data["unitDiscountValue"]
    assert line["unitDiscountType"] == line_discount_data["unitDiscountType"]
    assert line["unitDiscountReason"] == line_discount_data["unitDiscountReason"]
    assert line["unitDiscount"]["amount"] == line_discount_data["unitDiscountValue"]

    # Step 2 - Update delivery method
    address = DEFAULT_ADDRESS
    address["firstName"] = "New name"
    input = {
        "shippingMethod": shipping_method_id_2,
        "billingAddress": DEFAULT_ADDRESS,  # force the price recalculation
    }
    draft_order = draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )

    order_shipping_id = draft_order["order"]["deliveryMethod"]["id"]
    assert order_shipping_id == shipping_method_id_2
    order_billing_address = draft_order["order"]["billingAddress"]
    assert_address_data(order_billing_address, address)

    # Step 3 - Ensure that the line discount is still applied
    draft_order = order_query(e2e_staff_api_client, order_id)

    assert draft_order
    assert len(draft_order["lines"]) == 1
    line = draft_order["lines"][0]
    assert line["unitDiscountValue"] == line_discount_data["unitDiscountValue"]
    assert line["unitDiscountType"] == line_discount_data["unitDiscountType"]
    assert line["unitDiscountReason"] == line_discount_data["unitDiscountReason"]
    assert line["unitDiscount"]["amount"] == line_discount_data["unitDiscountValue"]
    assert (
        line["undiscountedUnitPrice"]["gross"]["amount"] * line["quantity"]
        - line["totalPrice"]["gross"]["amount"]
    ) / 5 == line["unitDiscount"]["amount"]
    assert (
        draft_order["subtotal"]["gross"]["amount"]
        == line["totalPrice"]["gross"]["amount"]
    )
