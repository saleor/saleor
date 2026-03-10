import graphene
from django.core.exceptions import ValidationError

from ....inventory.error_codes import ReceiptErrorCode
from ....inventory.models import Receipt as ReceiptModel
from ....inventory.receipt_workflow import complete_receipt
from ....permission.enums import WarehousePermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.utils import from_global_id_or_error
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import PurchaseOrderItemAdjustment, Receipt, ReceiptError


class ReceiptComplete(BaseMutation):
    """Complete a receipt and process any discrepancies."""

    receipt = graphene.Field(
        Receipt,
        description="The completed receipt.",
    )
    adjustments_pending = graphene.List(
        graphene.NonNull(PurchaseOrderItemAdjustment),
        description="Adjustments requiring manual review.",
        required=True,
    )
    discrepancies = graphene.Int(
        description="Number of items with discrepancies.",
        required=True,
    )

    class Arguments:
        receipt_id = graphene.ID(
            required=True,
            description="ID of the receipt to complete.",
        )

    class Meta:
        description = (
            "Complete a goods receipt. Automatically creates adjustments for "
            "discrepancies between ordered and received quantities."
        )
        permissions = (WarehousePermissions.MANAGE_STOCK,)
        error_type_class = ReceiptError
        error_type_field = "receipt_errors"
        doc_category = DOC_CATEGORY_PRODUCTS

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        receipt_id = data["receipt_id"]

        # Get receipt
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

        # Get plugin manager for notifications
        manager = get_plugin_manager_promise(info.context).get()

        # Complete receipt
        try:
            result = complete_receipt(
                receipt=receipt,
                user=info.context.user,
                manager=manager,
            )
        except ValidationError as e:
            from ....order.error_codes import OrderErrorCode

            code = getattr(e, "code", None)
            if code == OrderErrorCode.XERO_SYNC_FAILED.value:
                raise ValidationError(
                    {
                        "receipt_id": ValidationError(
                            str(e.message),
                            code=ReceiptErrorCode.XERO_SYNC_FAILED.value,
                        )
                    }
                ) from e
            msg = str(e.message) if hasattr(e, "message") else str(e)
            raise ValidationError(
                {
                    "receipt_id": ValidationError(
                        msg,
                        code=ReceiptErrorCode.INVALID.value,
                    )
                }
            ) from e
        except ValueError as e:
            raise ValidationError(
                {
                    "receipt_id": ValidationError(
                        str(e),
                        code=ReceiptErrorCode.INVALID.value,
                    )
                }
            ) from e

        return ReceiptComplete(
            receipt=result["receipt"],
            adjustments_pending=result["adjustments_pending"],
            discrepancies=result["discrepancies"],
        )
