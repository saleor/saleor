import pytest

from ..product.utils.preparing_product import prepare_product
from ..promotions.utils import promotions_query, update_promotion_rule
from ..sales.utils import (
    create_sale,
    create_sale_channel_listing,
    raw_create_sale_channel_listing,
    sale_catalogues_add,
)
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions


def prepare_sale_for_product(
    e2e_staff_api_client,
    channel_id,
    product_id,
    sale_discount_type,
    sale_discount_value,
):
    sale_name = "Sale"
    sale = create_sale(
        e2e_staff_api_client,
        sale_name,
        sale_discount_type,
    )
    sale_id = sale["id"]
    sale_listing_input = [
        {
            "channelId": channel_id,
            "discountValue": sale_discount_value,
        }
    ]
    create_sale_channel_listing(
        e2e_staff_api_client,
        sale_id,
        add_channels=sale_listing_input,
    )
    catalogue_input = {"products": [product_id]}
    sale_catalogues_add(
        e2e_staff_api_client,
        sale_id,
        catalogue_input,
    )

    return sale_id, sale_name, sale_discount_type, sale_discount_value


@pytest.mark.e2e
def test_sale_updated_by_promotion_can_not_be_handled_by_sales_core_2116(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    warehouse_id = shop_data["warehouse"]["id"]

    (
        product_id,
        _product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price="41.99",
    )

    (
        sale_id,
        sale_name,
        sale_discount_type,
        sale_discount_value,
    ) = prepare_sale_for_product(
        e2e_staff_api_client,
        channel_id,
        product_id,
        sale_discount_type="FIXED",
        sale_discount_value=30,
    )

    # Step 1 - Get promotions and check for created sale
    promotions = promotions_query(e2e_staff_api_client)
    sale_as_promotion = promotions[0]["node"]
    assert sale_as_promotion["name"] == sale_name
    sale_rule = sale_as_promotion["rules"][1]
    sale_rule_id = sale_rule["id"]
    assert sale_rule["rewardValue"] == sale_discount_value
    assert sale_rule["rewardValueType"] == sale_discount_type

    # Step 2 - Update sale by promotion rule mutation
    input = {
        "rewardValue": 25.0,
    }
    sale_as_promotion = update_promotion_rule(e2e_staff_api_client, sale_rule_id, input)
    assert sale_as_promotion["rewardValue"] == 25.0

    # Step 3 - Try to update sale channel listing using sale mutation
    sale_listing_input = [
        {
            "channelId": channel_id,
            "discountValue": 20,
        }
    ]
    sale_update = raw_create_sale_channel_listing(
        e2e_staff_api_client,
        sale_id,
        add_channels=sale_listing_input,
    )
    sale_update_error = sale_update["data"]["saleChannelListingUpdate"]["errors"]
    assert sale_update_error[0]["message"] == "Sale with given ID can't be found."
    assert sale_update_error[0]["field"] == "id"
    assert sale_update_error[0]["code"] == "NOT_FOUND"
