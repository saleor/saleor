import uuid

from ...channel.utils import create_channel, update_channel
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
from ...warehouse.utils import create_warehouse, update_warehouse
from ..utils.shop_update_settings import update_shop_settings


def create_and_update_tax_rates(e2e_staff_api_client, tax_rates):
    created_tax_classes = {}
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


def prepare_shop(e2e_staff_api_client, **kwargs):
    num_channels = kwargs.get("num_channels", 1)
    num_warehouses = kwargs.get("num_warehouses", 1)
    is_private = kwargs.get("is_private", False)
    click_and_collect_option = kwargs.get("click_and_collect_option", "DISABLED")
    currency = kwargs.get("currency", "USD")
    country = kwargs.get("country", "US")
    automatically_fulfill_non_shippable_giftcard = kwargs.get(
        "automatically_fulfill_non_shippable_giftcard", False
    )
    allow_unpaid_orders = kwargs.get("allow_unpaid_orders", False)
    automatically_confirm_all_new_orders = kwargs.get(
        "automaticallyConfirmAllNewOrders", True
    )
    mark_as_paid_strategy = kwargs.get("mark_as_paid_strategy", "PAYMENT_FLOW")
    expire_order_after_in_minutes = kwargs.get("expire_order_after_in_minutes", None)
    delete_expired_order_after_in_days = kwargs.get(
        "delete_expired_order_after_in_days", "1"
    )
    fulfillment_auto_approve = kwargs.get("fulfillment_auto_approve", False)
    fulfillment_allow_unpaid = kwargs.get("fulfillment_allow_unpaid", False)
    minimum_order_price = kwargs.get("minimum_order_price", None)
    maximum_order_price = kwargs.get("maximum_order_price", None)
    enable_account_confirmation_by_email = kwargs.get(
        "enable_account_confirmation_by_email", True
    )
    allow_login_without_confirmation = kwargs.get(
        "allow_login_without_confirmation", False
    )
    allow_unpaid_orders = kwargs.get("allow_unpaid_orders", False)
    shipping_zone_countries = kwargs.get("shipping_zone_countries", ["US"])
    shipping_zones_structure = kwargs.get(
        "shipping_zones_structure", [{"countries": ["US"], "num_shipping_methods": 1}]
    )
    billing_country_code = kwargs.get("billing_country_code", "US")
    shipping_country_code = kwargs.get("shipping_country_code", "US")
    shipping_price = kwargs.get("shipping_price", "10.00")
    billing_country_tax_rate = kwargs.get("billing_country_tax_rate")
    shipping_country_tax_rate = kwargs.get("shipping_country_tax_rate")
    country_tax_rate = kwargs.get("country_tax_rate")
    product_tax_rate = kwargs.get("product_tax_rate")
    product_type_tax_rate = kwargs.get("product_type_tax_rate")
    tax_calculation_strategy = kwargs.get("tax_calculation_strategy", "FLAT_RATES")
    display_gross_prices = kwargs.get("display_gross_prices", True)
    prices_entered_with_tax = kwargs.get("prices_entered_with_tax", True)
    created_warehouses = []
    created_channels = []
    created_shipping_zones = []
    created_shipping_methods = []
    created_shipping_methods_ids = []
    warehouse_id = None
    channel_id = None
    channel_slug = None
    shipping_zone_id = None
    shipping_method_id = None
    country_tax_class_id = kwargs.get("country_tax_class_id", None)
    shipping_tax_class_id = kwargs.get("shipping_tax_class_id", None)
    product_tax_class_id = kwargs.get("product_tax_class_id", None)
    product_type_tax_class_id = kwargs.get("product_type_tax_class_id", None)
    billing_tax_class_id = kwargs.get("billing_tax_class_id", None)

    for _ in range(num_warehouses):
        warehouse_data = create_warehouse(e2e_staff_api_client)
        warehouse_id = warehouse_data["id"]
        warehouse_ids = [warehouse_id]
        created_warehouses.append(warehouse_data)

        update_warehouse(
            e2e_staff_api_client,
            warehouse_data["id"],
            is_private=is_private,
            click_and_collect_option=click_and_collect_option,
        )
        if num_channels is not None:
            for i in range(num_channels):
                channel_slug = kwargs.get(
                    f"channel_slug_{i}", f"test_channel_{uuid.uuid4()}"
                )

                channel_data = create_channel(
                    e2e_staff_api_client,
                    slug=channel_slug,
                    warehouse_ids=warehouse_ids,
                    currency=currency,
                    country=country,
                    is_active=True,
                    automatically_fulfill_non_shippable_giftcard=automatically_fulfill_non_shippable_giftcard,
                    allow_unpaid_orders=allow_unpaid_orders,
                    automatically_confirm_all_new_orders=automatically_confirm_all_new_orders,
                    mark_as_paid_strategy=mark_as_paid_strategy,
                )
                channel_id = channel_data["id"]
                channel_ids = [channel_id]
                created_channels.append(
                    {"id": channel_data["id"], "slug": channel_slug}
                )

                channel_update_input = {
                    "orderSettings": {
                        "markAsPaidStrategy": mark_as_paid_strategy,
                        "automaticallyFulfillNonShippableGiftCard": automatically_fulfill_non_shippable_giftcard,
                        "allowUnpaidOrders": allow_unpaid_orders,
                        "automaticallyConfirmAllNewOrders": automatically_confirm_all_new_orders,
                        "expireOrdersAfter": expire_order_after_in_minutes,
                        "deleteExpiredOrdersAfter": delete_expired_order_after_in_days,
                    },
                }
                update_channel(
                    e2e_staff_api_client,
                    channel_id,
                    channel_update_input,
                )

                for zone_info in shipping_zones_structure:
                    zone_countries = zone_info["countries"]
                    shipping_zone_data = create_shipping_zone(
                        e2e_staff_api_client,
                        name=f"{zone_countries} shipping zone",
                        countries=zone_countries,
                        warehouse_ids=warehouse_ids,
                        channel_ids=channel_ids,
                    )
                    shipping_zone_id = shipping_zone_data["id"]
                    shipping_methods_for_zone = []

                    for _ in range(zone_info.get("num_shipping_methods", 1)):
                        shipping_method_data = create_shipping_method(
                            e2e_staff_api_client, shipping_zone_id
                        )
                        shipping_method_id = shipping_method_data["id"]

                        created_shipping_methods.append(shipping_method_data)
                        shipping_methods_for_zone.append(shipping_method_id)
                        created_shipping_methods_ids.append(shipping_method_id)

                        create_shipping_method_channel_listing(
                            e2e_staff_api_client,
                            shipping_method_id,
                            channel_id,
                            price=shipping_price,
                            minimum_order_price=minimum_order_price,
                            maximum_order_price=maximum_order_price,
                        )

                        shipping_zone_data[
                            "shippingMethods"
                        ] = shipping_methods_for_zone
                        created_shipping_zones.append(shipping_zone_data)

            tax_config_data = get_tax_configurations(e2e_staff_api_client)
            channel_tax_config = tax_config_data[0]["node"]
            tax_config_id = channel_tax_config["id"]

            update_tax_configuration(
                e2e_staff_api_client,
                tax_config_id,
                tax_calculation_strategy=tax_calculation_strategy,
                display_gross_prices=display_gross_prices,
                prices_entered_with_tax=prices_entered_with_tax,
            )

            tax_rates = [
                {
                    "type": "country",
                    "name": "Country Tax Class",
                    "country_code": country,
                    "rate": country_tax_rate,
                }
                if country_tax_rate is not None
                else None,
                {
                    "type": "shipping",
                    "name": "Shipping Tax Class",
                    "country_code": shipping_country_code,
                    "rate": shipping_country_tax_rate,
                }
                if shipping_country_tax_rate is not None
                else None,
                {
                    "type": "billing",
                    "name": "Billing Tax Class",
                    "country_code": billing_country_code,
                    "rate": billing_country_tax_rate,
                }
                if billing_country_tax_rate is not None
                else None,
                {
                    "type": "product",
                    "name": "Product Tax Class",
                    "country_code": country,
                    "rate": product_tax_rate,
                }
                if product_tax_rate is not None
                else None,
                {
                    "type": "product_type",
                    "name": "Product Type Tax Class",
                    "country_code": country,
                    "rate": product_type_tax_rate,
                }
                if product_type_tax_rate is not None
                else None,
            ]
            tax_rates = [rate for rate in tax_rates if rate is not None]

            created_tax_classes = create_and_update_tax_rates(
                e2e_staff_api_client, tax_rates
            )
            if "country" in created_tax_classes:
                country_tax_class_id = created_tax_classes["country"]["id"]

            if "shipping" in created_tax_classes:
                shipping_tax_class_id = created_tax_classes["shipping"]["id"]

            if "billing" in created_tax_classes:
                billing_tax_class_id = created_tax_classes["billing"]["id"]

            if "product" in created_tax_classes:
                product_tax_class_id = created_tax_classes["product"]["id"]
            if "product_type" in created_tax_classes:
                product_type_tax_class_id = created_tax_classes["product_type"]["id"]

            input_data = {
                "enableAccountConfirmationByEmail": enable_account_confirmation_by_email,
                "allowLoginWithoutConfirmation": allow_login_without_confirmation,
                "fulfillmentAutoApprove": fulfillment_auto_approve,
                "fulfillmentAllowUnpaid": fulfillment_allow_unpaid,
            }
            update_shop_settings(e2e_staff_api_client, input_data)

    return {
        "warehouse_id": warehouse_id,
        "channel_id": channel_id,
        "country": country,
        "channel_slug": channel_slug,
        "created_channels": created_channels,
        "shipping_zone_id": shipping_zone_id,
        "shipping_method_id": shipping_method_id,
        "shipping_method_ids": created_shipping_methods_ids,
        "shipping_price": shipping_price,
        "shipping_country_tax_rate": shipping_country_tax_rate,
        "billing_country_tax_rate": billing_country_tax_rate,
        "product_tax_rate": product_tax_rate,
        "product_type_tax_rate": product_type_tax_rate,
        "country_tax_rate": country_tax_rate,
        "shipping_tax_class_id": shipping_tax_class_id,
        "product_tax_class_id": product_tax_class_id,
        "product_type_tax_class_id": product_type_tax_class_id,
        "shipping_zone_countries": shipping_zone_countries,
        "shipping_country_code": shipping_country_code,
        "billing_country_code": billing_country_code,
        "created_shipping_zones": created_shipping_zones,
        "billing_tax_class_id": billing_tax_class_id,
        "country_tax_class_id": country_tax_class_id,
        "expire_order_after_in_minutes": expire_order_after_in_minutes,
        "delete_expired_order_after_in_days": delete_expired_order_after_in_days,
    }
