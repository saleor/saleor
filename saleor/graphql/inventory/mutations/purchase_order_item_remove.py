import graphene
from django.core.exceptions import ValidationError

from ....inventory import PurchaseOrderStatus, models
from ....inventory.error_codes import PurchaseOrderErrorCode
from ....permission.enums import WarehousePermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.utils import from_global_id_or_error
from ..types import PurchaseOrder, PurchaseOrderError


class RemovePurchaseOrderItem(BaseMutation):
    purchase_order = graphene.Field(
        PurchaseOrder, description="The parent purchase order."
    )

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the purchase order item to remove."
        )

    class Meta:
        description = "Removes an item from a draft purchase order."
        permissions = (WarehousePermissions.MANAGE_PURCHASE_ORDERS,)
        error_type_class = PurchaseOrderError
        error_type_field = "purchase_order_errors"
        doc_category = DOC_CATEGORY_PRODUCTS

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        _, pk = from_global_id_or_error(data["id"], "PurchaseOrderItem")

        try:
            poi = models.PurchaseOrderItem.objects.select_related("order").get(pk=pk)
        except models.PurchaseOrderItem.DoesNotExist:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Purchase order item not found.",
                        code=PurchaseOrderErrorCode.NOT_FOUND.value,
                    )
                }
            ) from None

        if poi.order.status != PurchaseOrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Only items on draft purchase orders can be removed.",
                        code=PurchaseOrderErrorCode.INVALID.value,
                    )
                }
            )

        purchase_order = poi.order

        # Also clean up any PORAs linked to this POI's variant on this PO
        models.PurchaseOrderRequestedAllocation.objects.filter(
            purchase_order=purchase_order,
            allocation__stock__product_variant=poi.product_variant,
        ).delete()

        poi.delete()

        return RemovePurchaseOrderItem(purchase_order=purchase_order)
