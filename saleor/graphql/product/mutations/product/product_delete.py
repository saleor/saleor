import graphene

from .....attribute import AttributeInputType
from .....attribute import models as attribute_models
from .....core.permissions import ProductPermissions
from .....core.tracing import traced_atomic_transaction
from .....order import events as order_events
from .....order import models as order_models
from .....order.tasks import recalculate_orders_task
from .....product import models
from ....app.dataloaders import load_app
from ....channel import ChannelContext
from ....core.mutations import ModelDeleteMutation
from ....core.types import ProductError
from ....plugins.dataloaders import load_plugin_manager
from ...types import Product
from ...utils import get_draft_order_lines_data_for_variants


class ProductDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product to delete.")

    class Meta:
        description = "Deletes a product."
        model = models.Product
        object_type = Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        node_id = data.get("id")

        instance = cls.get_node_or_error(info, node_id, only_type=Product)
        variants_id = list(instance.variants.all().values_list("id", flat=True))
        with traced_atomic_transaction():
            cls.delete_assigned_attribute_values(instance)

            draft_order_lines_data = get_draft_order_lines_data_for_variants(
                variants_id
            )

            response = super().perform_mutation(_root, info, **data)

            # delete order lines for deleted variant
            order_models.OrderLine.objects.filter(
                pk__in=draft_order_lines_data.line_pks
            ).delete()

            app = load_app(info.context)
            # run order event for deleted lines
            for (
                order,
                order_lines,
            ) in draft_order_lines_data.order_to_lines_mapping.items():
                order_events.order_line_product_removed_event(
                    order, info.context.user, app, order_lines
                )

            order_pks = draft_order_lines_data.order_pks
            manager = load_plugin_manager(info.context)
            if order_pks:
                recalculate_orders_task.delay(list(order_pks))
            cls.call_event(manager.product_deleted, instance, variants_id)

        return response

    @staticmethod
    def delete_assigned_attribute_values(instance):
        attribute_models.AttributeValue.objects.filter(
            productassignments__product_id=instance.id,
            attribute__input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES,
        ).delete()
