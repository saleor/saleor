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
    channels=None,
    shop_settings=None,
    tax_settings=None,
):
    if shop_settings is not None:
        update_shop_settings(e2e_staff_api_client, input_data=shop_settings)

    warehouse_id = create_warehouse(e2e_staff_api_client)["id"]

    created_channels = []
    for channel_index, channel in enumerate(channels):
        if channel is None:
            channel = []
        created_channel = create_channel(
            e2e_staff_api_client,
            order_settings=channel["order_settings"],
            warehouse_ids=[warehouse_id],
        )
        channel_id = created_channel["id"]
        created_channels.append(
            {
                "id": channel_id,
                "warehouse_id": warehouse_id,
                "slug": created_channel["slug"],
                "shipping_zones": [],
                "order_settings": created_channel["orderSettings"],
            }
        )

        for shipping_zone_index, shipping_zone in enumerate(channel["shipping_zones"]):
            created_shipping_zone = create_shipping_zone(
                e2e_staff_api_client,
                warehouse_ids=[warehouse_id],
                channel_ids=[channel_id],
                countries=shipping_zone.get("countries"),
            )

            created_channels[channel_index]["shipping_zones"].append(
                {
                    "id": created_shipping_zone["id"],
                    "shipping_methods": [],
                }
            )

            for shipping_zone in shipping_zone["shipping_methods"]:
                created_shipping_method = create_shipping_method(
                    e2e_staff_api_client,
                    shipping_zone_id=created_shipping_zone["id"],
                    name=shipping_zone.get("name"),
                )

                created_channels[channel_index]["shipping_zones"][shipping_zone_index][
                    "shipping_methods"
                ].append({"id": created_shipping_method["id"]})

                create_shipping_method_channel_listing(
                    e2e_staff_api_client,
                    shipping_method_id=created_shipping_method["id"],
                    channel_id=created_channel["id"],
                    add_channels=shipping_zone.get("add_channels", None),
                )
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
    tax_config = [created_tax_classes, tax_rates]
    return created_channels, tax_config


def prepare_default_shop(
    e2e_staff_api_client,
):
    created_warehouse = create_warehouse(e2e_staff_api_client)

    created_channel = create_channel(
        e2e_staff_api_client,
        warehouse_ids=[created_warehouse["id"]],
    )

    created_shipping_zone = create_shipping_zone(
        e2e_staff_api_client,
        warehouse_ids=[created_warehouse["id"]],
        channel_ids=[created_channel["id"]],
    )

    created_shipping_method = create_shipping_method(
        e2e_staff_api_client,
        shipping_zone_id=created_shipping_zone["id"],
    )

    _ = create_shipping_method_channel_listing(
        e2e_staff_api_client,
        shipping_method_id=created_shipping_method["id"],
        channel_id=created_channel["id"],
        add_channels={},
    )

    return {
        "warehouse": created_warehouse,
        "channel": created_channel,
        "shipping_zone": created_shipping_zone,
        "shipping_method": created_shipping_method,
    }
