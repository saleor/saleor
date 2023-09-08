import pytest

from ..product.utils import (
    create_collection,
    create_collection_channel_listing,
    create_product_variant,
    create_product_variant_channel_listing,
    get_product,
)
from ..product.utils.collection_add_products import add_product_to_collection
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
    promotion_rule_name="Test rule",
    collection_ids=None,
    channel_id=None,
):
    promotion_name = "Promotion Test"
    promotion_data = create_promotion(e2e_staff_api_client, promotion_name)
    promotion_id = promotion_data["id"]

    predicate_input = {"collectionPredicate": {"ids": collection_ids}}
    promotion_rule_data = create_promotion_rule(
        e2e_staff_api_client,
        promotion_id,
        predicate_input,
        discount_type,
        discount_value,
        promotion_rule_name,
        channel_id,
    )
    promotion_rule_id = promotion_rule_data["id"]
    discount_value = promotion_rule_data["rewardValue"]

    return promotion_rule_id, discount_value


@pytest.mark.e2e
def test_staff_can_change_catalogue_predicate_core_2112(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_shipping,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_shipping,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    warehouse_id, channel_id, channel_slug, _ = prepare_shop(e2e_staff_api_client)

    product_id, product_variant_id, _ = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, "7.99"
    )

    collection_data = create_collection(e2e_staff_api_client)
    collection_id = collection_data["id"]
    create_collection_channel_listing(e2e_staff_api_client, collection_id, channel_id)
    add_product_to_collection(e2e_staff_api_client, collection_id, [product_id])

    promotion_rule_id, discount_value = prepare_promotion(
        e2e_staff_api_client,
        30,
        "PERCENTAGE",
        collection_ids=[collection_id],
        channel_id=channel_id,
    )

    # Step 1 Create new variant and listing channel for it
    variant_data = create_product_variant(
        e2e_staff_api_client,
        product_id,
    )
    second_product_variant_id = variant_data["id"]

    second_variant_price = "20.99"
    create_product_variant_channel_listing(
        e2e_staff_api_client,
        second_product_variant_id,
        channel_id,
        second_variant_price,
    )

    # Step 2 Update promotion rule of new variant
    input = {
        "cataloguePredicate": {
            "collectionPredicate": {},
            "variantPredicate": {"ids": [second_product_variant_id]},
        }
    }
    update_promotion_rule(e2e_staff_api_client, promotion_rule_id, input)

    # Step 3 Check if promotion is applied to new variant
    product_data = get_product(e2e_staff_api_client, product_id, channel_slug)
    first_variant = product_data["variants"][0]
    assert first_variant["id"] == product_variant_id
    second_variant = product_data["variants"][1]
    assert second_variant["id"] == second_product_variant_id
    assert product_data["pricing"]["onSale"] is False
    assert first_variant["pricing"]["onSale"] is False
    assert second_variant["pricing"]["onSale"] is True
    calculated_second_variant_discount = round(
        float(second_variant_price) * (discount_value / 100), 2
    )
    assert (
        second_variant["pricing"]["discount"]["gross"]["amount"]
        == calculated_second_variant_discount
    )
    assert second_variant["pricing"]["priceUndiscounted"]["gross"]["amount"] == float(
        second_variant_price
    )
