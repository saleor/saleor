import pytest

from ....product.tasks import recalculate_discounted_price_for_products_task
from ..promotions.utils import (
    create_promotion,
    create_promotion_rule,
    delete_promotion,
    promotion_query,
)
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils.preparing_product import prepare_product
from .utils.product_query import get_product


@pytest.mark.e2e
def test_product_no_longer_on_promotion_when_promotion_is_removed_CORE_2114(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]

    (
        product_id,
        product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, variant_price=20
    )
    promotion_name = "Promotion Fixed"
    discount_value = 5
    discount_type = "FIXED"
    promotion_rule_name = "rule for product"
    promotion_type = "CATALOGUE"
    promotion_data = create_promotion(
        e2e_staff_api_client, promotion_name, promotion_type
    )
    promotion_id = promotion_data["id"]

    catalogue_predicate = {"productPredicate": {"ids": [product_id]}}

    input = {
        "promotion": promotion_id,
        "channels": [channel_id],
        "name": promotion_rule_name,
        "cataloguePredicate": catalogue_predicate,
        "rewardValue": discount_value,
        "rewardValueType": discount_type,
    }
    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        input,
    )
    product_predicate = promotion_rule["cataloguePredicate"]["productPredicate"]["ids"]
    assert promotion_rule["channels"][0]["id"] == channel_id
    assert product_predicate[0] == product_id

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Step 1 - Check product is on promotion
    product_data = get_product(e2e_staff_api_client, product_id, channel_slug)
    assert product_data["id"] == product_id
    assert product_data["pricing"]["onSale"] is True
    variant_data = product_data["variants"][0]
    variant_id = product_data["variants"][0]["id"]
    assert variant_id == product_variant_id
    assert variant_data["pricing"]["onSale"] is True

    # Step 2 - Remove the promotion and check the product is not on promotion
    delete_promotion(e2e_staff_api_client, promotion_id)
    data = promotion_query(e2e_staff_api_client, promotion_id)
    assert data["promotion"] is None

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Step 3 - Check product in no longer on promotion
    product_data = get_product(e2e_staff_api_client, product_id, channel_slug)
    assert product_data["id"] == product_id
    assert product_data["pricing"]["onSale"] is False
    variant_data = product_data["variants"][0]
    variant_id = product_data["variants"][0]["id"]
    assert variant_id == product_variant_id
    assert variant_data["pricing"]["onSale"] is False
