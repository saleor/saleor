from . import (
    create_category,
    create_digital_content,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
)


def prepare_product(
    e2e_staff_api_client,
    warehouse_id,
    channel_id,
    variant_price,
):
    product_type_data = create_product_type(
        e2e_staff_api_client,
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(e2e_staff_api_client)
    category_id = category_data["id"]

    product_data = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
    )
    product_id = product_data["id"]

    create_product_channel_listing(
        e2e_staff_api_client,
        product_id,
        channel_id,
    )

    stocks = [
        {
            "warehouse": warehouse_id,
            "quantity": 5,
        }
    ]
    product_variant_data = create_product_variant(
        e2e_staff_api_client,
        product_id,
        stocks=stocks,
    )
    product_variant_id = product_variant_data["id"]

    product_variant_channel_listing_data = create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id,
        channel_id,
        variant_price,
    )
    product_variant_price = product_variant_channel_listing_data["channelListings"][0][
        "price"
    ]["amount"]

    return product_id, product_variant_id, product_variant_price


def prepare_digital_product(
    e2e_staff_api_client,
    channel_id,
    warehouse_id,
    variant_price,
):
    product_type_data = create_product_type(
        e2e_staff_api_client,
        is_shipping_required=False,
        is_digital=True,
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(e2e_staff_api_client)
    category_id = category_data["id"]

    product_data = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
    )
    product_id = product_data["id"]

    create_product_channel_listing(
        e2e_staff_api_client,
        product_id,
        channel_id,
    )

    stocks = [
        {
            "warehouse": warehouse_id,
            "quantity": 5,
        }
    ]
    product_variant_data = create_product_variant(
        e2e_staff_api_client,
        product_id,
        stocks=stocks,
    )
    product_variant_id = product_variant_data["id"]

    variant_listing = create_product_variant_channel_listing(
        e2e_staff_api_client, product_variant_id, channel_id, price=10
    )

    create_digital_content(e2e_staff_api_client, product_variant_id)

    product_variant_price = variant_listing["channelListings"][0]["price"]["amount"]
    return product_id, product_variant_id, product_variant_price
