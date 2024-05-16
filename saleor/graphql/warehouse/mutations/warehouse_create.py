from ....permission.enums import ProductPermissions
from ....warehouse import models
from ...account.i18n import I18nMixin
from ...account.mixins import AddressMetadataMixin
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import WarehouseError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Warehouse, WarehouseCreateInput
from .base import WarehouseMixin


class WarehouseCreate(AddressMetadataMixin, WarehouseMixin, ModelMutation, I18nMixin):
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
    def prepare_address(cls, cleaned_input, info):
        address_data = cleaned_input["address"]
        address_instance = cls.validate_address(address_data, info=info)
        address_instance.save()
        return address_instance

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.warehouse_created, instance)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance = cls.get_instance(info, **data)
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        cleaned_input["address"] = cls.prepare_address(cleaned_input, info)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input)
        cls.post_save_action(info, instance, cleaned_input)
        return cls.success_response(instance)
