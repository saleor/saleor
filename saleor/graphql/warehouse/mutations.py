import graphene

from saleor.account.models import Address
from saleor.graphql.core.mutations import ModelDeleteMutation, ModelMutation
from saleor.graphql.core.types.common import WarehouseError
from saleor.graphql.warehouse.types import WarehouseCreateInput, WarehouseUpdateInput
from saleor.warehouse import models

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


class WarehouseCreate(ModelMutation):
    class Arguments:
        input = WarehouseCreateInput(
            required=True, description="Fields required to create warehouse."
        )

    class Meta:
        description = "Creates new warehouse."
        model = models.Warehouse
        permissions = ("warehouse.manage_warehouses",)

    @classmethod
    def create_address(cls, clean_data):
        address_data = clean_data["address"]
        address = Address.objects.create(**address_data)
        return address

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        cleaned_data = super().clean_input(info, instance, data, input_cls=input_cls)
        cleaned_data["address"] = cls.create_address(cleaned_data)
        return cleaned_data


class WarehouseUpdate(ModelMutation):
    class Meta:
        model = models.Warehouse
        permissions = ("warehouse.manage_warehouses",)
        description = "Update given warehouse."

    class Arguments:
        id = graphene.ID(description="ID of a warehouse to update.", required=True)
        input = WarehouseUpdateInput()

    @classmethod
    def update_address(cls, instance, cleaned_data):
        address = instance.address
        address_data = cleaned_data.get("address")
        if address_data is None:
            return address
        for field in ADDRESS_FIELDS:
            field_value = address_data.get(field)
            if field_value is not None:
                setattr(address, field, field_value)
        address.save()
        return address

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        cleaned_data = super().clean_input(info, instance, data, input_cls=input_cls)
        cleaned_data["address"] = cls.update_address(instance, cleaned_data)
        return cleaned_data


class WarehouseDelete(ModelDeleteMutation):
    class Meta:
        model = models.Warehouse
        permissions = ("warehouse.manage_warehouses",)
        description = "Deletes selected warehouse."
        error_type_class = WarehouseError
        error_type_field = "warehouse_errors"

    class Arguments:
        id = graphene.ID(description="ID of a warehouse to delete.", required=True)
