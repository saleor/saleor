import graphene
from django.core.exceptions import ValidationError

from ...shipping.models import ShippingZone
from ...warehouse import models
from ..account.i18n import I18nMixin
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.types.common import WarehouseError
from .types import WarehouseCreateInput, WarehouseUpdateInput

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
    def validate_warehouse_count(cls, shipping_zones, instance):
        warehouses = set(
            ShippingZone.objects.filter(
                id__in=[shipping_zone.id for shipping_zone in shipping_zones]
            )
            .filter(warehouse__isnull=False)
            .values_list("warehouse", flat=True)
        )
        if not bool(warehouses):
            return True
        if len(warehouses) > 1:
            return False
        if instance.id is None:
            return False
        return warehouses == {instance.id}

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        shipping_zones = cleaned_input.get("shipping_zones", [])
        if not cls.validate_warehouse_count(shipping_zones, instance):
            msg = "Shipping zone can be assigned only to one warehouse."
            raise ValidationError({"shipping_zones": msg})
        return cleaned_input

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        cleaned_data["address"] = cls.prepare_address(cleaned_data, instance)
        return super().construct_instance(instance, cleaned_data)


class WarehouseCreate(WarehouseMixin, ModelMutation, I18nMixin):
    class Arguments:
        input = WarehouseCreateInput(
            required=True, description="Fields required to create warehouse."
        )

    class Meta:
        description = "Creates new warehouse."
        model = models.Warehouse
        permissions = ("warehouse.manage_warehouses",)
        error_type_class = WarehouseError
        error_type_field = "warehouse_errors"

    @classmethod
    def prepare_address(cls, cleaned_data, *args):
        address_form = cls.validate_address_form(cleaned_data["address"])
        return address_form.save()


class WarehouseUpdate(WarehouseMixin, ModelMutation, I18nMixin):
    class Meta:
        model = models.Warehouse
        permissions = ("warehouse.manage_warehouses",)
        description = "Update given warehouse."
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


class WarehouseDelete(ModelDeleteMutation):
    class Meta:
        model = models.Warehouse
        permissions = ("warehouse.manage_warehouses",)
        description = "Deletes selected warehouse."
        error_type_class = WarehouseError
        error_type_field = "warehouse_errors"

    class Arguments:
        id = graphene.ID(description="ID of a warehouse to delete.", required=True)
