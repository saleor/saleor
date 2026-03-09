import graphene
from django.core.exceptions import ValidationError

from ....inventory.error_codes import ReceiptErrorCode
from ....inventory.models import Receipt as ReceiptModel
from ....inventory.receipt_workflow import delay_for_future_shipment
from ....permission.enums import WarehousePermissions
from ....product.models import Product
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.utils import from_global_id_or_error
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import PurchaseOrderItem, ReceiptError


class DelayForFutureShipment(BaseMutation):
    """Delay unreceived POIs for a product, removing them from this shipment."""

    delayed_items = graphene.List(
        graphene.NonNull(PurchaseOrderItem),
        description="The POIs that were delayed.",
    )

    class Arguments:
        receipt_id = graphene.ID(
            required=True,
            description="ID of the completed receipt.",
        )
        product_id = graphene.ID(
            required=True,
            description="ID of the product to delay.",
        )

    class Meta:
        description = (
            "Delay unreceived purchase order items for a product. "
            "Removes them from the current shipment and reverts to CONFIRMED "
            "status so they can be assigned to a future shipment. "
            "Deletes the auto-created POIAs since no real adjustment occurred. "
            "Only works for POIs with 0 quantity received."
        )
        permissions = (WarehousePermissions.MANAGE_STOCK,)
        error_type_class = ReceiptError
        error_type_field = "receipt_errors"
        doc_category = DOC_CATEGORY_PRODUCTS

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        receipt_id = data["receipt_id"]
        product_id = data["product_id"]

        _, receipt_pk = from_global_id_or_error(receipt_id, "Receipt")
        try:
            receipt = ReceiptModel.objects.get(pk=receipt_pk)
        except ReceiptModel.DoesNotExist:
            raise ValidationError(
                {
                    "receipt_id": ValidationError(
                        "Receipt not found.",
                        code=ReceiptErrorCode.NOT_FOUND.value,
                    )
                }
            ) from None

        _, product_pk = from_global_id_or_error(product_id, "Product")
        try:
            product = Product.objects.get(pk=product_pk)
        except Product.DoesNotExist:
            raise ValidationError(
                {
                    "product_id": ValidationError(
                        "Product not found.",
                        code=ReceiptErrorCode.NOT_FOUND.value,
                    )
                }
            ) from None

        manager = get_plugin_manager_promise(info.context).get()

        try:
            delayed_pois = delay_for_future_shipment(
                receipt=receipt,
                product=product,
                user=info.context.user,
                manager=manager,
            )
        except ValueError as e:
            raise ValidationError(
                {
                    "product_id": ValidationError(
                        str(e),
                        code=ReceiptErrorCode.INVALID.value,
                    )
                }
            ) from e

        return DelayForFutureShipment(delayed_items=delayed_pois)
