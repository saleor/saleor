import pytest

from ....product.tasks import recalculate_discounted_price_for_products_task
from ..product.utils import (
    get_product,
    raw_create_product_channel_listing,
    raw_create_product_variant_channel_listing,
)
from ..product.utils.preparing_product import prepare_product
from ..promotions.utils import (
    create_promotion,
    create_promotion_rule,
    update_promotion_rule,
)
from ..shop.utils.preparing_shop import prepare_shop
from ..utils import assign_permissions


def prepare_promotion(
    e2e_staff_api_client,
    discount_value,
    discount_type,
    predicate_input,
    promotion_rule_name="Test rule",
    channel_id=None,
):
    promotion_name = "Promotion Test"
    promotion_type = "CATALOGUE"
    promotion_data = create_promotion(
        e2e_staff_api_client, promotion_name, promotion_type
    )
    promotion_id = promotion_data["id"]

    input = {
        "promotion": promotion_id,
        "channels": [channel_id],
        "name": promotion_rule_name,
        "cataloguePredicate": predicate_input,
        "rewardValue": discount_value,
        "rewardValueType": "PERCENTAGE",
    }

    promotion_rule = create_promotion_rule(e2e_staff_api_client, input)
    promotion_rule_id = promotion_rule["id"]
    discount_value = promotion_rule["rewardValue"]

    return promotion_rule_id


def prepare_channels_with_product(e2e_staff_api_client):
    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "countries": ["US"],
                        "name": "us shipping zone",
                        "shipping_methods": [{}],
                    },
                ],
                "order_settings": {},
            },
            {
                "shipping_zones": [
                    {
                        "countries": ["PL"],
                        "name": "pl shipping zone",
                        "shipping_methods": [{}],
                    },
                ],
                "order_settings": {},
            },
        ],
        shop_settings={},
    )
    us_channel_id = shop_data[0]["id"]
    us_channel_slug = shop_data[0]["slug"]
    pl_channel_id = shop_data[1]["id"]
    pl_channel_slug = shop_data[1]["slug"]
    warehouse_id = shop_data[0]["warehouse_id"]

    product_id, product_variant_id, _ = prepare_product(
        e2e_staff_api_client, warehouse_id, us_channel_id, "7.99"
    )

    product_listing_data = raw_create_product_channel_listing(
        e2e_staff_api_client,
        product_id,
        pl_channel_id,
        is_published=True,
        visible_in_listings=True,
        is_available_for_purchase=True,
    )
    assert (
        product_listing_data["product"]["channelListings"][1]["channel"]["id"]
        == pl_channel_id
    )

    variant_listing_data = raw_create_product_variant_channel_listing(
        e2e_staff_api_client, product_variant_id, pl_channel_id, price="99"
    )
    assert (
        variant_listing_data["variant"]["channelListings"][1]["channel"]["id"]
        == pl_channel_id
    )
    return (
        us_channel_id,
        us_channel_slug,
        pl_channel_id,
        pl_channel_slug,
        product_id,
    )


@pytest.mark.e2e
def test_staff_can_change_promotion_rule_channel_core_2113(
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

    (
        us_channel_id,
        us_channel_slug,
        pl_channel_id,
        pl_channel_slug,
        product_id,
    ) = prepare_channels_with_product(e2e_staff_api_client)

    predicate_input = {"productPredicate": {"ids": [product_id]}}
    promotion_rule_id = prepare_promotion(
        e2e_staff_api_client,
        50,
        "PERCENTAGE",
        predicate_input,
        channel_id=[us_channel_id],
    )

    # Step 1 Update promotion rule: switch channels
    update_promotion_rule(
        e2e_staff_api_client,
        promotion_rule_id,
        input={
            "addChannels": [pl_channel_id],
            "removeChannels": [us_channel_id],
            "cataloguePredicate": predicate_input,
        },
    )

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Step 2 Check if promotion is applied for product on second channel
    product_data_channel_2 = get_product(
        e2e_staff_api_client, product_id, pl_channel_slug
    )
    assert product_data_channel_2["pricing"]["onSale"] is True
    variant = product_data_channel_2["variants"][0]
    assert variant["pricing"]["discount"]["gross"]["amount"] == 49.5

    # Step 3 Check if promotion is not applied for product on first channel
    product_data_channel_1 = get_product(
        e2e_staff_api_client, product_id, us_channel_slug
    )
    assert product_data_channel_1["pricing"]["onSale"] is False
