import graphene

from ....core.tracing import traced_atomic_transaction
from ....permission.enums import ProductPermissions
from ....warehouse import models
from ...core import ResolveInfo
from ...core.mutations import ModelDeleteMutation
from ...core.types import WarehouseError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Warehouse


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
