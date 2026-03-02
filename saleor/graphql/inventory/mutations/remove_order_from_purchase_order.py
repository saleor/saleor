import graphene
from django.core.exceptions import ValidationError

from ....inventory import PurchaseOrderStatus, models
from ....inventory.error_codes import PurchaseOrderErrorCode
from ....inventory.stock_management import remove_order_from_purchase_order
from ....order.models import Order
from ....permission.enums import WarehousePermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.utils import from_global_id_or_error
from ..types import PurchaseOrder, PurchaseOrderError


class RemoveOrderFromPurchaseOrder(BaseMutation):
    purchase_order = graphene.Field(
        PurchaseOrder, description="The updated purchase order."
    )

    class Arguments:
        order_id = graphene.ID(required=True, description="ID of the order to unlink.")
        purchase_order_id = graphene.ID(
            required=True, description="ID of the draft purchase order."
        )

    class Meta:
        description = (
            "Removes an order's linkage from a draft purchase order, "
            "deleting PORAs and reducing POI quantities accordingly."
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
                        code=PurchaseOrderErrorCode.NOT_FOUND.value,
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
                        code=PurchaseOrderErrorCode.NOT_FOUND.value,
                    )
                }
            ) from None

        if purchase_order.status != PurchaseOrderStatus.DRAFT:
            raise ValidationError(
                {
                    "purchase_order_id": ValidationError(
                        "Only draft purchase orders can be modified.",
                        code=PurchaseOrderErrorCode.INVALID.value,
                    )
                }
            )

        linked = models.PurchaseOrderRequestedAllocation.objects.filter(
            purchase_order=purchase_order,
            allocation__order_line__order=order,
        ).exists()
        if not linked:
            raise ValidationError(
                {
                    "order_id": ValidationError(
                        "This order is not linked to this purchase order.",
                        code=PurchaseOrderErrorCode.INVALID.value,
                    )
                }
            )

        remove_order_from_purchase_order(order, purchase_order)
        purchase_order.refresh_from_db()

        return RemoveOrderFromPurchaseOrder(purchase_order=purchase_order)
