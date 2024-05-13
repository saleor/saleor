import graphene

from ....core.taxes import zero_taxed_money
from ....core.tracing import traced_atomic_transaction
from ....order import events
from ....order.error_codes import OrderErrorCode
from ....order.fetch import OrderLineInfo
from ....order.search import update_order_search_vector
from ....order.utils import (
    delete_order_line,
    invalidate_order_prices,
    recalculate_order_weight,
)
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...core.utils import raise_validation_error
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order, OrderLine
from .utils import EditableOrderValidationMixin, get_webhook_handler_by_order_status


class OrderLineDelete(EditableOrderValidationMixin, BaseMutation):
    order = graphene.Field(Order, description="A related order.")
    order_line = graphene.Field(
        OrderLine, description="An order line that was deleted."
    )

    class Arguments:
        id = graphene.ID(description="ID of the order line to delete.", required=True)

    class Meta:
        description = "Deletes an order line from an order."
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id
    ):
        manager = get_plugin_manager_promise(info.context).get()
        line = cls.get_node_or_error(
            info,
            id,
            only_type=OrderLine,
        )
        order = line.order
        cls.validate(info, order, line)

        db_id = line.id
        line_allocation = line.allocations.first()
        warehouse_pk = (
            line_allocation.stock.warehouse.pk
            if line_allocation and order.is_unconfirmed()
            else None
        )
        with traced_atomic_transaction():
            line_info = OrderLineInfo(
                line=line,
                quantity=line.quantity,
                variant=line.variant,
                warehouse_pk=warehouse_pk,
            )
            delete_order_line(line_info, manager)
            line.id = db_id

            updated_fields = []
            if not order.is_shipping_required():
                order.shipping_method = None
                order.shipping_price = zero_taxed_money(order.currency)
                order.shipping_method_name = None
                updated_fields = [
                    "currency",
                    "shipping_method",
                    "shipping_price_net_amount",
                    "shipping_price_gross_amount",
                    "shipping_method_name",
                    "updated_at",
                ]
            # Create the removal event
            app = get_app_promise(info.context).get()
            events.order_removed_products_event(
                order=order,
                user=info.context.user,
                app=app,
                order_lines=[line],
            )

            invalidate_order_prices(order)
            recalculate_order_weight(order)
            update_order_search_vector(order, save=False)
            updated_fields.extend(
                ["should_refresh_prices", "weight", "search_vector", "updated_at"]
            )
            order.save(update_fields=updated_fields)
            func = get_webhook_handler_by_order_status(order.status, manager)
            cls.call_event(func, order)
        return OrderLineDelete(order=order, order_line=line)

    @classmethod
    def validate(cls, info, order, line):
        cls.check_channel_permissions(info, [order.channel_id])
        cls.validate_order(line.order)
        if line.is_gift:
            raise_validation_error(
                message="Order line marked as gift can't be deleted.",
                field="id",
                code=OrderErrorCode.NON_REMOVABLE_GIFT_LINE.value,
            )
