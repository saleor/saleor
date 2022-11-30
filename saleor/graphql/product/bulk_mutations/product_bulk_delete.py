from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from ....attribute import AttributeInputType
from ....attribute import models as attribute_models
from ....core.permissions import ProductPermissions
from ....core.tracing import traced_atomic_transaction
from ....order import events as order_events
from ....order import models as order_models
from ....order.tasks import recalculate_orders_task
from ....product import models
from ...app.dataloaders import load_app
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import NonNullList, ProductError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Product
from ..utils import get_draft_order_lines_data_for_variants


class ProductBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of product IDs to delete."
        )

    class Meta:
        description = "Deletes products."
        model = models.Product
        object_type = Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, ids, **data):
        try:
            pks = cls.get_global_ids_or_error(ids, Product)
        except ValidationError as error:
            return 0, error
        product_to_variant = list(
            models.ProductVariant.objects.filter(product__pk__in=pks).values_list(
                "product_id", "id"
            )
        )
        variants_ids = [variant_id for _, variant_id in product_to_variant]

        cls.delete_assigned_attribute_values(pks)

        draft_order_lines_data = get_draft_order_lines_data_for_variants(variants_ids)

        response = super().perform_mutation(
            _root,
            info,
            ids,
            product_to_variant=product_to_variant,
            **data,
        )

        # delete order lines for deleted variants
        order_models.OrderLine.objects.filter(
            pk__in=draft_order_lines_data.line_pks
        ).delete()

        app = load_app(info.context)
        # run order event for deleted lines
        for order, order_lines in draft_order_lines_data.order_to_lines_mapping.items():
            order_events.order_line_product_removed_event(
                order, info.context.user, app, order_lines
            )

        order_pks = draft_order_lines_data.order_pks
        if order_pks:
            recalculate_orders_task.delay(list(order_pks))

        return response

    @staticmethod
    def delete_assigned_attribute_values(instance_pks):
        attribute_models.AttributeValue.objects.filter(
            productassignments__product_id__in=instance_pks,
            attribute__input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES,
        ).delete()

    @classmethod
    def bulk_action(cls, info, queryset, product_to_variant):
        product_variant_map = defaultdict(list)
        for product, variant in product_to_variant:
            product_variant_map[product].append(variant)

        products = [product for product in queryset]
        queryset.delete()
        manager = load_plugin_manager(info.context)
        for product in products:
            variants = product_variant_map.get(product.id, [])
            manager.product_deleted(product, variants)
