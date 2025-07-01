import graphene
from django.db.models.expressions import Exists, OuterRef

from .....attribute import AttributeInputType
from .....attribute import models as attribute_models
from .....core.tracing import traced_atomic_transaction
from .....order import events as order_events
from .....order import models as order_models
from .....order.tasks import recalculate_orders_task
from .....permission.enums import ProductPermissions
from .....product import models
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.context import ChannelContext
from ....core.mutations import ModelDeleteMutation, ModelWithExtRefMutation
from ....core.types import ProductError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Product
from ...utils import get_draft_order_lines_data_for_variants


class ProductDelete(ModelDeleteMutation, ModelWithExtRefMutation):
    class Arguments:
        id = graphene.ID(required=False, description="ID of a product to delete.")
        external_reference = graphene.String(
            required=False,
            description="External ID of a product to delete.",
        )

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
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, external_reference=None, id=None
    ):
        instance = cls.get_instance(info, external_reference=external_reference, id=id)
        with traced_atomic_transaction():
            variants_id = list(
                instance.variants.order_by("pk")
                .select_for_update(of=("self",))
                .all()
                .values_list("id", flat=True)
            )
            cls.delete_assigned_attribute_values(instance)

            draft_order_lines_data = get_draft_order_lines_data_for_variants(
                variants_id
            )

            models.ProductVariant.objects.order_by("pk").filter(
                pk__in=variants_id
            ).delete()
            response = super().perform_mutation(
                _root, info, external_reference=external_reference, id=id
            )

            # delete order lines for deleted variant
            order_models.OrderLine.objects.filter(
                pk__in=draft_order_lines_data.line_pks
            ).delete()

            app = get_app_promise(info.context).get()
            # run order event for deleted lines
            for (
                order,
                order_lines,
            ) in draft_order_lines_data.order_to_lines_mapping.items():
                order_events.order_line_product_removed_event(
                    order, info.context.user, app, order_lines
                )

            order_pks = draft_order_lines_data.order_pks
            manager = get_plugin_manager_promise(info.context).get()
            if order_pks:
                recalculate_orders_task.delay(list(order_pks))
            cls.call_event(manager.product_deleted, instance, variants_id)

        return response

    @staticmethod
    def delete_assigned_attribute_values(instance):
        assigned_values = attribute_models.AssignedProductAttributeValue.objects.filter(
            product_id=instance.pk
        )
        attributes = attribute_models.Attribute.objects.filter(
            input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES
        )

        attribute_models.AttributeValue.objects.filter(
            Exists(assigned_values.filter(value_id=OuterRef("id"))),
            Exists(attributes.filter(id=OuterRef("attribute_id"))),
        ).delete()
