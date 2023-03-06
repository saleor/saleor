from collections import defaultdict
from typing import List

import graphene
from django.core.exceptions import ValidationError

from ...channel import models as channel_models
from ...core.permissions import ProductPermissions
from ...core.tracing import traced_atomic_transaction
from ...warehouse import WarehouseClickAndCollectOption, models
from ...warehouse.error_codes import WarehouseErrorCode
from ...warehouse.validation import validate_warehouse_count
from ..account.i18n import I18nMixin
from ..core import ResolveInfo
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.types import NonNullList, WarehouseError
from ..core.validators import (
    validate_required_string_field,
    validate_slug_and_generate_if_needed,
)
from ..plugins.dataloaders import get_plugin_manager_promise
from ..shipping.types import ShippingZone
from .types import Warehouse, WarehouseCreateInput, WarehouseUpdateInput

ADDRESS_FIELDS = [
    "street_address_1",
    "street_address_2",
    "city",
    "city_area",
    "postal_code",
    "country",
    "country_area",
    "phone",
]


class WarehouseMixin:
    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(  # type: ignore[misc] # mixin
            info, instance, data, **kwargs
        )
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = WarehouseErrorCode.REQUIRED.value
            raise ValidationError({"slug": error})

        if "name" in cleaned_input:
            try:
                cleaned_input = validate_required_string_field(cleaned_input, "name")
            except ValidationError as error:
                error.code = WarehouseErrorCode.REQUIRED.value
                raise ValidationError({"name": error})

        # assigning shipping zones in the WarehouseCreate mutation is deprecated
        if cleaned_input.get("shipping_zones"):
            raise ValidationError(
                {
                    "shipping_zones": ValidationError(
                        "The shippingZone input field is deprecated. "
                        "Use WarehouseShippingZoneAssign mutation",
                        code=WarehouseErrorCode.INVALID.value,
                    )
                }
            )

        click_and_collect_option = cleaned_input.get(
            "click_and_collect_option", instance.click_and_collect_option
        )
        is_private = cleaned_input.get("is_private", instance.is_private)
        if (
            click_and_collect_option == WarehouseClickAndCollectOption.LOCAL_STOCK
            and is_private
        ):
            msg = "Local warehouse can be toggled only for non-private warehouse stocks"
            raise ValidationError(
                {
                    "click_and_collect_option": ValidationError(
                        msg, code=WarehouseErrorCode.INVALID.value
                    )
                },
            )
        return cleaned_input

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        cleaned_data["address"] = cls.prepare_address(cleaned_data, instance)  # type: ignore[attr-defined] # mixing # noqa: E501
        return super().construct_instance(instance, cleaned_data)  # type: ignore[misc] # mixing # noqa: E501


class WarehouseCreate(WarehouseMixin, ModelMutation, I18nMixin):
    class Arguments:
        input = WarehouseCreateInput(
            required=True, description="Fields required to create warehouse."
        )

    class Meta:
        description = "Creates new warehouse."
        model = models.Warehouse
        object_type = Warehouse
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = WarehouseError
        error_type_field = "warehouse_errors"

    @classmethod
    def prepare_address(cls, cleaned_data, *args):
        address_form = cls.validate_address_form(cleaned_data["address"])
        return address_form.save()

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.warehouse_created, instance)


class WarehouseShippingZoneAssign(ModelMutation, I18nMixin):
    class Meta:
        model = models.Warehouse
        object_type = Warehouse
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        description = "Add shipping zone to given warehouse."
        error_type_class = WarehouseError
        error_type_field = "warehouse_errors"

    class Arguments:
        id = graphene.ID(description="ID of a warehouse to update.", required=True)
        shipping_zone_ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of shipping zone IDs.",
        )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, shipping_zone_ids: List[str]
    ):
        warehouse = cls.get_node_or_error(info, id, only_type=Warehouse)
        shipping_zones = cls.get_nodes_or_error(
            shipping_zone_ids, "shipping_zone_id", only_type=ShippingZone
        )
        cls.clean_shipping_zones(warehouse, shipping_zones)
        warehouse.shipping_zones.add(*shipping_zones)
        return WarehouseShippingZoneAssign(warehouse=warehouse)

    @classmethod
    def clean_shipping_zones(cls, instance, shipping_zones):
        if not validate_warehouse_count(shipping_zones, instance):
            msg = "Shipping zone can be assigned only to one warehouse."
            raise ValidationError(
                {"shipping_zones": msg}, code=WarehouseErrorCode.INVALID.value
            )

        cls.check_if_zones_can_be_assigned(instance, shipping_zones)

    @classmethod
    def check_if_zones_can_be_assigned(cls, instance, shipping_zones):
        """Check if all shipping zones to add has common channel with warehouse.

        Raise and error when the condition is not fulfilled.
        """
        shipping_zone_ids = [zone.id for zone in shipping_zones]
        ChannelShippingZone = channel_models.Channel.shipping_zones.through  # type: ignore[attr-defined] # raw access to the through model # noqa: E501
        channel_shipping_zones = ChannelShippingZone.objects.filter(
            shippingzone_id__in=shipping_zone_ids
        )

        # shipping zone cannot be assigned when any channel is assigned to the zone
        if not channel_shipping_zones:
            invalid_shipping_zone_ids = shipping_zone_ids

        zone_to_channel_mapping = defaultdict(set)
        for shipping_zone_id, channel_id in channel_shipping_zones.values_list(
            "shippingzone_id", "channel_id"
        ):
            zone_to_channel_mapping[shipping_zone_id].add(channel_id)

        WarehouseChannel = models.Warehouse.channels.through
        zone_channel_ids = set(
            WarehouseChannel.objects.filter(warehouse_id=instance.id).values_list(
                "channel_id", flat=True
            )
        )

        invalid_shipping_zone_ids = cls._find_invalid_shipping_zones(
            zone_to_channel_mapping, shipping_zone_ids, zone_channel_ids
        )

        if invalid_shipping_zone_ids:
            invalid_zones = {
                graphene.Node.to_global_id("ShippingZone", pk)
                for pk in invalid_shipping_zone_ids
            }
            raise ValidationError(
                {
                    "shipping_zones": ValidationError(
                        "Only warehouses that have common channel with shipping zone "
                        "can be assigned.",
                        code=WarehouseErrorCode.INVALID,
                        params={
                            "shipping_zones": invalid_zones,
                        },
                    )
                }
            )

    @staticmethod
    def _find_invalid_shipping_zones(
        zone_to_channel_mapping, shipping_zone_ids, warehouse_channel_ids
    ):
        invalid_warehouse_ids = []
        for zone_id in shipping_zone_ids:
            zone_channels = zone_to_channel_mapping.get(zone_id)
            # shipping zone cannot be added if it hasn't got any channel assigned
            # or if it does not have common channel with the warehouse
            if not zone_channels or not zone_channels.intersection(
                warehouse_channel_ids
            ):
                invalid_warehouse_ids.append(zone_id)
        return invalid_warehouse_ids


class WarehouseShippingZoneUnassign(ModelMutation, I18nMixin):
    class Meta:
        model = models.Warehouse
        object_type = Warehouse
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        description = "Remove shipping zone from given warehouse."
        error_type_class = WarehouseError
        error_type_field = "warehouse_errors"

    class Arguments:
        id = graphene.ID(description="ID of a warehouse to update.", required=True)
        shipping_zone_ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of shipping zone IDs.",
        )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, shipping_zone_ids: List[str]
    ):
        warehouse = cls.get_node_or_error(info, id, only_type=Warehouse)
        shipping_zones = cls.get_nodes_or_error(
            shipping_zone_ids, "shipping_zone_id", only_type=ShippingZone
        )
        warehouse.shipping_zones.remove(*shipping_zones)
        return WarehouseShippingZoneAssign(warehouse=warehouse)


class WarehouseUpdate(WarehouseMixin, ModelMutation, I18nMixin):
    class Meta:
        model = models.Warehouse
        object_type = Warehouse
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        description = "Updates given warehouse."
        error_type_class = WarehouseError
        error_type_field = "warehouse_errors"

    class Arguments:
        id = graphene.ID(description="ID of a warehouse to update.", required=True)
        input = WarehouseUpdateInput(
            required=True, description="Fields required to update warehouse."
        )

    @classmethod
    def prepare_address(cls, cleaned_data, instance):
        address_data = cleaned_data.get("address")
        address = instance.address
        if address_data is None:
            return address
        address_form = cls.validate_address_form(address_data, instance=address)
        return address_form.save()

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.warehouse_updated, instance)


class WarehouseDelete(ModelDeleteMutation):
    class Meta:
        model = models.Warehouse
        object_type = Warehouse
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        description = "Deletes selected warehouse."
        error_type_class = WarehouseError
        error_type_field = "warehouse_errors"

    class Arguments:
        id = graphene.ID(description="ID of a warehouse to delete.", required=True)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        manager = get_plugin_manager_promise(info.context).get()
        node_id = data.get("id")
        model_type = cls.get_type_for_model()
        instance = cls.get_node_or_error(info, node_id, only_type=model_type)

        if instance:
            cls.clean_instance(info, instance)

        stocks = (stock for stock in instance.stock_set.only("product_variant"))
        address_id = instance.address_id
        address = instance.address

        db_id = instance.id
        with traced_atomic_transaction():
            instance.delete()

            # After the instance is deleted, set its ID to the original database's
            # ID so that the success response contains ID of the deleted object.
            # Additionally, assign copy of deleted Address object to allow fetching
            # address data on success response or in subscription webhook query.
            instance.id = db_id
            address.id = address_id
            instance.address = address

            # Set `is_object_deleted` attribute to use it in Warehouse object type
            # resolvers and for example decide if we should use Dataloader to resolve
            # address or return object directly.
            instance.is_object_deleted = True

            cls.post_save_action(info, instance, None)
            for stock in stocks:
                cls.call_event(manager.product_variant_out_of_stock, stock)
        return cls.success_response(instance)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.warehouse_deleted, instance)
