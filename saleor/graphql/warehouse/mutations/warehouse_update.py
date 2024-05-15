import graphene

from ....permission.enums import ProductPermissions
from ....warehouse import models
from ...account.i18n import I18nMixin
from ...account.mixins import AddressMetadataMixin
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_316
from ...core.mutations import ModelWithExtRefMutation
from ...core.types import WarehouseError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Warehouse, WarehouseUpdateInput
from .base import WarehouseMixin


class WarehouseUpdate(
    AddressMetadataMixin, WarehouseMixin, ModelWithExtRefMutation, I18nMixin
):
    class Meta:
        model = models.Warehouse
        object_type = Warehouse
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        description = "Updates given warehouse."
        error_type_class = WarehouseError
        error_type_field = "warehouse_errors"

    class Arguments:
        id = graphene.ID(description="ID of a warehouse to update.", required=False)
        input = WarehouseUpdateInput(
            required=True, description="Fields required to update warehouse."
        )
        external_reference = graphene.String(
            required=False,
            description="External reference of a warehouse." + ADDED_IN_316,
        )

    @classmethod
    def prepare_address(cls, cleaned_input, instance, info):
        address_instance = instance.address
        address_data = cleaned_input.get("address", {})
        if not address_data:
            return address_instance
        address_instance = cls.validate_address(
            address_data, info=info, instance=address_instance
        )
        address_instance.save()
        return address_instance

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.warehouse_updated, instance)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance = cls.get_instance(info, **data)
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        cleaned_input["address"] = cls.prepare_address(cleaned_input, instance, info)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input)
        cls.post_save_action(info, instance, cleaned_input)
        return cls.success_response(instance)
