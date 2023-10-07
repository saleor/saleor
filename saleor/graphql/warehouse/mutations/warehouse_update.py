import graphene

from ....permission.enums import ProductPermissions
from ....warehouse import models
from ...account.i18n import I18nMixin
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_316
from ...core.mutations import ModelWithExtRefMutation
from ...core.types import WarehouseError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Warehouse, WarehouseUpdateInput
from .base import WarehouseMixin


class WarehouseUpdate(WarehouseMixin, ModelWithExtRefMutation):
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
    def prepare_address(cls, cleaned_data, instance):
        address_data = cleaned_data.get("address")
        address_metadata = list()
        if address_data:
            address_metadata = address_data.pop("metadata", list())
        address = instance.address
        if address_data is None:
            return address
        address_form = I18nMixin.validate_address_form(address_data, instance=address)
        if address_metadata:
            cls.update_metadata(address, address_metadata)
        return address_form.save()

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.warehouse_updated, instance)
