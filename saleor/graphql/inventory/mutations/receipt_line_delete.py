import graphene
from django.core.exceptions import ValidationError

from ....inventory.error_codes import ReceiptErrorCode
from ....inventory.exceptions import ReceiptLineNotInProgress
from ....inventory.models import ReceiptLine as ReceiptLineModel
from ....inventory.receipt_workflow import delete_receipt_line
from ....permission.enums import WarehousePermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.utils import from_global_id_or_error
from ..types import ReceiptError


class ReceiptLineDelete(BaseMutation):
    """Delete a receipt line (undo a scanned item)."""

    class Arguments:
        receipt_line_id = graphene.ID(
            required=True,
            description="ID of the receipt line to delete.",
        )

    class Meta:
        description = (
            "Delete a receipt line and revert the quantity update. "
            "Use when an item was scanned by mistake."
        )
        permissions = (WarehousePermissions.MANAGE_STOCK,)
        error_type_class = ReceiptError
        error_type_field = "receipt_errors"
        doc_category = DOC_CATEGORY_PRODUCTS

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        receipt_line_id = data["receipt_line_id"]

        # Get receipt line
        _, line_pk = from_global_id_or_error(receipt_line_id, "ReceiptLine")
        try:
            receipt_line = ReceiptLineModel.objects.select_related("receipt").get(
                pk=line_pk
            )
        except ReceiptLineModel.DoesNotExist:
            raise ValidationError(
                {
                    "receipt_line_id": ValidationError(
                        "Receipt line not found.",
                        code=ReceiptErrorCode.NOT_FOUND.value,
                    )
                }
            ) from None

        # Delete line
        try:
            delete_receipt_line(receipt_line)
        except ReceiptLineNotInProgress as e:
            raise ValidationError(
                {
                    "receipt_line_id": ValidationError(
                        str(e),
                        code=ReceiptErrorCode.INVALID.value,
                    )
                }
            ) from e

        return ReceiptLineDelete()
