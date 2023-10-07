import graphene
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from ....channel import models
from ....channel.error_codes import ChannelErrorCode
from ....core.tracing import traced_atomic_transaction
from ....permission.enums import (
    ChannelPermissions,
    CheckoutPermissions,
    OrderPermissions,
    PaymentPermissions,
)
from ....shipping.tasks import (
    drop_invalid_shipping_methods_relations_for_given_channels,
)
from ....webhook.event_types import WebhookEventAsyncType
from ...account.enums import CountryCodeEnum
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_31, ADDED_IN_35
from ...core.doc_category import DOC_CATEGORY_CHANNELS
from ...core.mutations import ModelMutation
from ...core.types import ChannelError, NonNullList
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils.validators import check_for_duplicates
from ..types import Channel
from ..utils import delete_invalid_warehouse_to_shipping_zone_relations
from .channel_create import ChannelInput
from .utils import (
    clean_input_checkout_settings,
    clean_input_order_settings,
    clean_input_payment_settings,
)


class ChannelUpdateInput(ChannelInput):
    name = graphene.String(description="Name of the channel.")
    slug = graphene.String(description="Slug of the channel.")
    default_country = CountryCodeEnum(
        description=(
            "Default country for the channel. Default country can be "
            "used in checkout to determine the stock quantities or calculate taxes "
            "when the country was not explicitly provided." + ADDED_IN_31
        )
    )
    remove_shipping_zones = NonNullList(
        graphene.ID,
        description="List of shipping zones to unassign from the channel.",
        required=False,
    )
    remove_warehouses = NonNullList(
        graphene.ID,
        description="List of warehouses to unassign from the channel." + ADDED_IN_35,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_CHANNELS


class ChannelUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a channel to update.")
        input = ChannelUpdateInput(
            description="Fields required to update a channel.", required=True
        )

    class Meta:
        description = (
            "Update a channel.\n\n"
            "Requires one of the following permissions: MANAGE_CHANNELS.\n"
            "Requires one of the following permissions "
            "when updating only `orderSettings` field: "
            "`MANAGE_CHANNELS`, `MANAGE_ORDERS`.\n"
            "Requires one of the following permissions "
            "when updating only `checkoutSettings` field: "
            "`MANAGE_CHANNELS`, `MANAGE_CHECKOUTS`.\n"
            "Requires one of the following permissions "
            "when updating only `paymentSettings` field: "
            "`MANAGE_CHANNELS`, `HANDLE_PAYMENTS`."
        )
        auto_permission_message = False
        model = models.Channel
        object_type = Channel
        error_type_class = ChannelError
        error_type_field = "channel_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHANNEL_UPDATED,
                description="A channel was updated.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHANNEL_METADATA_UPDATED,
                description=(
                    "Optionally triggered when public or private metadata is updated."
                ),
            ),
        ]
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        errors = {}
        if error := check_for_duplicates(
            data, "add_shipping_zones", "remove_shipping_zones", "shipping_zones"
        ):
            error.code = ChannelErrorCode.DUPLICATED_INPUT_ITEM.value
            errors["shipping_zones"] = error

        if error := check_for_duplicates(
            data, "add_warehouses", "remove_warehouses", "warehouses"
        ):
            error.code = ChannelErrorCode.DUPLICATED_INPUT_ITEM.value
            errors["warehouses"] = error

        if errors:
            raise ValidationError(errors)

        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        slug = cleaned_input.get("slug")
        if slug:
            cleaned_input["slug"] = slugify(slug)
        if stock_settings := cleaned_input.get("stock_settings"):
            cleaned_input["allocation_strategy"] = stock_settings["allocation_strategy"]
        if order_settings := cleaned_input.get("order_settings"):
            clean_input_order_settings(order_settings, cleaned_input)

        if checkout_settings := cleaned_input.get("checkout_settings"):
            clean_input_checkout_settings(checkout_settings, cleaned_input)

        if payment_settings := cleaned_input.get("payment_settings"):
            clean_input_payment_settings(payment_settings, cleaned_input)

        return cleaned_input

    @classmethod
    def check_permissions(cls, context, permissions=None, **data):
        permissions = [ChannelPermissions.MANAGE_CHANNELS]
        has_permission = super().check_permissions(
            context, permissions, require_all_permissions=False, **data
        )
        if has_permission:
            return has_permission

        # Validate if user/app has enough permissions to update the specific settings.
        input = data["data"]["input"]

        settings_per_permission_map = {
            "order_settings": OrderPermissions.MANAGE_ORDERS,
            "checkout_settings": CheckoutPermissions.MANAGE_CHECKOUTS,
            "payment_settings": PaymentPermissions.HANDLE_PAYMENTS,
        }

        if set(input.keys()).difference(settings_per_permission_map.keys()):
            # user/app doesn't have MANAGE_CHANNELS and input contains not only
            # settings fields.
            return False

        permissions = []
        for key in input.keys():
            permissions.append(settings_per_permission_map[key])

        if not permissions:
            return False
        return super().check_permissions(
            context, permissions, require_all_permissions=True, **data
        )

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with traced_atomic_transaction():
            super()._save_m2m(info, instance, cleaned_data)
            cls._update_shipping_zones(instance, cleaned_data)
            cls._update_warehouses(instance, cleaned_data)
            if (
                "remove_shipping_zones" in cleaned_data
                or "remove_warehouses" in cleaned_data
            ):
                warehouse_ids = [
                    warehouse.id
                    for warehouse in cleaned_data.get("remove_warehouses", [])
                ]
                shipping_zone_ids = [
                    warehouse.id
                    for warehouse in cleaned_data.get("remove_shipping_zones", [])
                ]
                delete_invalid_warehouse_to_shipping_zone_relations(
                    instance, warehouse_ids, shipping_zone_ids
                )

    @classmethod
    def _update_shipping_zones(cls, instance, cleaned_data):
        add_shipping_zones = cleaned_data.get("add_shipping_zones")
        if add_shipping_zones:
            instance.shipping_zones.add(*add_shipping_zones)
        remove_shipping_zones = cleaned_data.get("remove_shipping_zones")
        if remove_shipping_zones:
            instance.shipping_zones.remove(*remove_shipping_zones)
            shipping_channel_listings = instance.shipping_method_listings.filter(
                shipping_method__shipping_zone__in=remove_shipping_zones
            )
            shipping_method_ids = list(
                shipping_channel_listings.values_list("shipping_method_id", flat=True)
            )
            shipping_channel_listings.delete()
            drop_invalid_shipping_methods_relations_for_given_channels.delay(
                shipping_method_ids, [instance.id]
            )

    @classmethod
    def _update_warehouses(cls, instance, cleaned_data):
        add_warehouses = cleaned_data.get("add_warehouses")
        if add_warehouses:
            instance.warehouses.add(*add_warehouses)
        remove_warehouses = cleaned_data.get("remove_warehouses")
        if remove_warehouses:
            instance.warehouses.remove(*remove_warehouses)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.channel_updated, instance)
        if cleaned_input.get("metadata"):
            cls.call_event(manager.channel_metadata_updated, instance)
