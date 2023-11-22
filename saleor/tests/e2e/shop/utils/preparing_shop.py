import base64

from ...channel.utils import create_channel
from ...shipping_zone.utils import (
    create_shipping_method,
    create_shipping_method_channel_listing,
    create_shipping_zone,
)
from ...taxes.utils import (
    create_tax_class,
    get_tax_configurations,
    update_tax_class,
    update_tax_configuration,
)
from ...warehouse.utils import create_warehouse
from ..utils.shop_update_settings import update_shop_settings


def decode_and_modify_base64_descriptor(encoded_string, new_descriptor=None):
    base64_bytes = encoded_string.encode("ascii")
    decoded_bytes = base64.b64decode(base64_bytes)
    decoded_string = decoded_bytes.decode("ascii")

    modified_string = decoded_string
    if new_descriptor:
        parts = decoded_string.split(":")
        if len(parts) >= 2:
            modified_string = f"{new_descriptor}:{parts[1]}"

    modified_base64 = base64.b64encode(modified_string.encode("ascii")).decode("ascii")

    padding = "=" * ((4 - len(modified_base64) % 4) % 4)
    modified_base64_padded = modified_base64 + padding

    return decoded_string, modified_base64_padded


def create_and_update_tax_classes(e2e_staff_api_client, tax_rates):
    created_tax_classes = {rate["type"]: {} for rate in tax_rates}

    for tax_rate_info in tax_rates:
        tax_class_data = create_tax_class(
            e2e_staff_api_client,
            tax_rate_info["name"],
            [
                {
                    "countryCode": tax_rate_info["country_code"],
                    "rate": tax_rate_info["rate"],
                }
            ],
        )
        created_tax_classes[tax_rate_info["type"]] = {
            "id": tax_class_data["id"],
            "rate": tax_rate_info["rate"],
        }

        tax_class_update_input = {
            "updateCountryRates": [
                {
                    "countryCode": tax_rate_info["country_code"],
                    "rate": tax_rate_info["rate"],
                }
            ]
        }
        update_tax_class(
            e2e_staff_api_client, tax_class_data["id"], tax_class_update_input
        )

    return created_tax_classes


def prepare_shop(
    e2e_staff_api_client,
    warehouses=None,
    channels_settings=None,
    shipping_zones=None,
    shipping_methods=None,
    shop_settings_update=None,
    tax_settings=None,
    shipping_method_channel_listing_settings={},
    **kwargs,
):
    if warehouses is None:
        warehouses = [create_warehouse(e2e_staff_api_client, **kwargs)]
    created_channels = []
    if channels_settings:
        for channel_config in channels_settings:
            channel = create_channel(
                e2e_staff_api_client,
                warehouse_ids=[warehouses[0]["id"]],
                **channel_config,
            )
            created_channels.append(channel)
    else:
        default_channel = create_channel(
            e2e_staff_api_client, warehouse_ids=[warehouses[0]["id"]], **kwargs
        )
        created_channels.append(default_channel)
    shipping_zones = []
    if shipping_zones is not None:
        for shipping_zone in shipping_zones:
            created = create_shipping_zone(
                e2e_staff_api_client,
                warehouse_ids=[w["id"] for w in warehouses],
                channel_ids=[c["id"] for c in created_channels],
                countries=shipping_zone.get("countries"),
            )
            shipping_zones.append(created)
    else:
        shipping_zones.append(
            create_shipping_zone(
                e2e_staff_api_client,
                warehouse_ids=[w["id"] for w in warehouses],
                channel_ids=[c["id"] for c in created_channels],
            )
        )

    if shipping_methods is None:
        shipping_methods = []
        for shipping_zone in shipping_zones:
            shipping_method_data = create_shipping_method(
                e2e_staff_api_client, shipping_zone_id=shipping_zone["id"], **kwargs
            )
            _, modified_encoded_id = decode_and_modify_base64_descriptor(
                shipping_method_data["id"], "ShippingMethod"
            )
            shipping_method_data["id"] = modified_encoded_id

            for channel in created_channels:
                channel_listing_data = create_shipping_method_channel_listing(
                    e2e_staff_api_client,
                    shipping_method_id=modified_encoded_id,
                    channel_id=channel["id"],
                    price=shipping_method_channel_listing_settings.get(
                        "price", "10.00"
                    ),
                    minimum_order_price=shipping_method_channel_listing_settings.get(
                        "minimumOrderPrice", None
                    ),
                    maximum_order_price=shipping_method_channel_listing_settings.get(
                        "maximumOrderPrice", None
                    ),
                    **kwargs,
                )
                if channel_listing_data.get("channelListings"):
                    price_info = channel_listing_data["channelListings"][0].get(
                        "price", {}
                    )
                    shipping_price = price_info.get("amount")
                    shipping_method_data["price"] = shipping_price

            shipping_methods.append(shipping_method_data)

    if shop_settings_update is not None:
        update_shop_settings(e2e_staff_api_client, input_data=shop_settings_update)

    created_tax_classes = {}
    tax_rates = {}
    if tax_settings:
        tax_rates_list = tax_settings.pop("tax_rates", [])
        tax_rates = {rate["type"]: rate for rate in tax_rates_list}

        tax_config_data = get_tax_configurations(e2e_staff_api_client)
        channel_tax_config = tax_config_data[0]["node"]
        tax_config_id = channel_tax_config["id"]
        update_tax_configuration(e2e_staff_api_client, tax_config_id, **tax_settings)

        if tax_rates:
            tax_classes_result = create_and_update_tax_classes(
                e2e_staff_api_client, tax_rates.values()
            )
            for tax_type, tax_rate in tax_rates.items():
                tax_class_id = tax_classes_result.get(tax_type, {}).get("id")
                if tax_class_id:
                    created_tax_classes[f"{tax_type}_tax_class_id"] = tax_class_id

    return {
        "warehouses": warehouses,
        "channels": created_channels,
        "shipping_zones": shipping_zones,
        "shipping_methods": shipping_methods,
        "tax_classes": created_tax_classes,
        "tax_rates": tax_rates,
        "shop_settings": shop_settings_update,
    }
