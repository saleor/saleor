import pytest

from ..channel.utils import create_channel
from ..product.utils import (
    create_category,
    create_collection,
    create_collection_channel_listing,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
    get_product,
)
from ..promotions.utils import (
    create_promotion,
    create_promotion_rule,
    update_promotion_rule,
)
from ..utils import assign_permissions


def prepare_product(
    e2e_staff_api_client,
    channel_slug,
    variant_price,
):
    channel_data = create_channel(
        e2e_staff_api_client,
        slug=channel_slug,
    )
    channel_id = channel_data["id"]

    product_type_data = create_product_type(
        e2e_staff_api_client,
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(
        e2e_staff_api_client,
    )
    category_id = category_data["id"]

    collection_data = create_collection(e2e_staff_api_client)
    collection_id = collection_data["id"]
    collection_list = [collection_id]

    create_collection_channel_listing(e2e_staff_api_client, collection_id, channel_id)
    product_data = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
        collection_ids=collection_list,
    )
    product_id = product_data["id"]
    create_product_channel_listing(e2e_staff_api_client, product_id, channel_id)

    variant_data = create_product_variant(
        e2e_staff_api_client,
        product_id,
    )
    product_variant_id = variant_data["id"]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id,
        channel_id,
        variant_price,
    )

    return product_id, channel_id, collection_id


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
def test_create_promotion_for_collection_core_2109(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    channel_slug = "promotion_collections_channel"
    variant_price = "7.99"
    product_id, channel_id, collection_id = prepare_product(
        e2e_staff_api_client,
        channel_slug,
        variant_price,
    )

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

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        second_product_variant_id,
        channel_id,
        variant_price,
    )

    # Step 2 Update promotion rule of new variant
    catalogue_predicate = {
        "productPredicate": {},
        "variantPredicate": {"ids": [second_product_variant_id]},
    }
    update_promotion_rule(e2e_staff_api_client, promotion_rule_id, catalogue_predicate)

    # Step 3 Check if promotion is applied to new variant
    product_data = get_product(e2e_staff_api_client, product_id, channel_slug)
    first_variant = product_data["variants"][0]
    second_variant = product_data["variants"][1]

    assert product_data["pricing"]["onSale"] is True
    assert first_variant["pricing"]["onSale"] is False
    assert second_variant["pricing"]["onSale"] is True
    calculated_variant_discount = round(
        float(variant_price) * (discount_value / 100), 2
    )
    assert (
        second_variant["pricing"]["discount"]["gross"]["amount"]
        == calculated_variant_discount
    )
    assert second_variant["pricing"]["priceUndiscounted"]["gross"]["amount"] == float(
        variant_price
    )
