import json

import pytest

from ..product.utils.preparing_product import prepare_product
from ..sales.utils import (
    create_sale,
    raw_create_sale_channel_listing,
    sale_catalogues_add,
)
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import promotions_query, translate_promotion


def prepare_sale(e2e_staff_api_client):
    price = 10

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]

    (
        product_id,
        _product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        price,
    )

    sale = create_sale(
        e2e_staff_api_client,
        name="Test sale",
        sale_type="PERCENTAGE",
    )
    sale_id = sale["id"]
    sale_name = sale["name"]

    sale_listing_input = [
        {
            "channelId": channel_id,
            "discountValue": 25,
        }
    ]
    raw_create_sale_channel_listing(
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

    return (
        channel_id,
        channel_slug,
        sale_name,
        sale_id,
    )


@pytest.mark.e2e
def test_unable_to_query_nor_mutate_sale_updated_by_promotion_translations_CORE_2120(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_translations,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_translations,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    (
        channel_id,
        channel_slug,
        sale_name,
        sale_id,
    ) = prepare_sale(e2e_staff_api_client)

    # Step 1 - Run promotions query
    promotions = promotions_query(
        e2e_staff_api_client,
        first=10,
        sort_by={
            "field": "CREATED_AT",
            "direction": "DESC",
        },
    )
    promotion_rule_id = promotions[0]["node"]["rules"][0]["id"]
    promotion_id = promotions[0]["node"]["id"]
    assert promotion_id != sale_id
    assert promotion_rule_id is not None
    assert promotions[0]["node"]["name"] == sale_name

    # Step 2 - Run mutation promotionTranslate
    promotion_translated_description = {
        "blocks": [{"data": {"text": "Promocja przetłumaczona"}, "type": "paragraph"}],
        "version": "1.0.0",
    }
    promotion_translate_input = {
        "name": "Promocja Testowa",
        "description": promotion_translated_description,
    }
    promotion_translation_data = translate_promotion(
        e2e_staff_api_client, promotion_id, "PL", promotion_translate_input
    )

    assert promotion_translation_data["language"]["code"] == "PL"
    assert promotion_translation_data["name"] == "Promocja Testowa"
    assert promotion_translation_data["description"] == json.dumps(
        promotion_translated_description
    )

    # Step 3 - Run mutation saleChannelListingUpdate
    sale_listing_input = [
        {
            "channelId": channel_id,
            "discountValue": 5,
        }
    ]
    sale_channel_listing_update = raw_create_sale_channel_listing(
        e2e_staff_api_client,
        sale_id,
        add_channels=sale_listing_input,
    )
    sale_error = sale_channel_listing_update["data"]["saleChannelListingUpdate"][
        "errors"
    ]
    assert sale_error[0]["message"] == "Sale with given ID can't be found."
    assert sale_error[0]["code"] == "NOT_FOUND"
    assert sale_error[0]["field"] == "id"
