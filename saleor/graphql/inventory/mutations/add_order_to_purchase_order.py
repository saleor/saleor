import graphene
from django.core.exceptions import ValidationError

from ....inventory import PurchaseOrderStatus, models
from ....inventory.error_codes import PurchaseOrderErrorCode
from ....inventory.stock_management import add_order_to_purchase_order
from ....order import OrderStatus
from ....order.models import Order
from ....permission.enums import WarehousePermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.utils import from_global_id_or_error
from ..types import PurchaseOrder, PurchaseOrderError


class AddOrderToPurchaseOrder(BaseMutation):
    purchase_order = graphene.Field(
        PurchaseOrder, description="The updated purchase order."
    )

    class Arguments:
        order_id = graphene.ID(
            required=True,
            description="ID of the order to link.",
        )
        purchase_order_id = graphene.ID(
            required=True,
            description="ID of the draft purchase order.",
        )

    class Meta:
        description = (
            "Links an order's allocations to a draft purchase order, "
            "creating PurchaseOrderRequestedAllocations and POIs as needed."
        )
        permissions = (WarehousePermissions.MANAGE_PURCHASE_ORDERS,)
        error_type_class = PurchaseOrderError
        error_type_field = "purchase_order_errors"
        doc_category = DOC_CATEGORY_PRODUCTS

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        _, order_pk = from_global_id_or_error(data["order_id"], "Order")
        _, po_pk = from_global_id_or_error(data["purchase_order_id"], "PurchaseOrder")

        try:
            order = Order.objects.get(pk=order_pk)
        except Order.DoesNotExist:
            raise ValidationError(
                {
                    "order_id": ValidationError(
                        "Order not found.",
                        code=PurchaseOrderErrorCode.GRAPHQL_ERROR.value,
                    )
                }
            ) from None

        try:
            purchase_order = models.PurchaseOrder.objects.get(pk=po_pk)
        except models.PurchaseOrder.DoesNotExist:
            raise ValidationError(
                {
                    "purchase_order_id": ValidationError(
                        "Purchase order not found.",
                        code=PurchaseOrderErrorCode.GRAPHQL_ERROR.value,
                    )
                }
            ) from None

        if purchase_order.status != PurchaseOrderStatus.DRAFT:
            raise ValidationError(
                {
                    "purchase_order_id": ValidationError(
                        "Purchase order must be in DRAFT status.",
                        code=PurchaseOrderErrorCode.GRAPHQL_ERROR.value,
                    )
                }
            )

        if order.status != OrderStatus.UNCONFIRMED:
            raise ValidationError(
                {
                    "order_id": ValidationError(
                        "Order must be in UNCONFIRMED status.",
                        code=PurchaseOrderErrorCode.GRAPHQL_ERROR.value,
                    )
                }
            )

        already_linked = models.PurchaseOrderRequestedAllocation.objects.filter(
            purchase_order__source_warehouse=purchase_order.source_warehouse,
            allocation__order_line__order=order,
        ).exists()
        if already_linked:
            raise ValidationError(
                {
                    "order_id": ValidationError(
                        "This order is already linked to a purchase order "
                        "for this supplier warehouse.",
                        code=PurchaseOrderErrorCode.INVALID.value,
                    )
                }
            )

        add_order_to_purchase_order(order, purchase_order)
        purchase_order.refresh_from_db()

        return AddOrderToPurchaseOrder(purchase_order=purchase_order)
