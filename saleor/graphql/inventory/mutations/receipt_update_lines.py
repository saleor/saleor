import graphene
from django.core.exceptions import ValidationError

from ....inventory.error_codes import ReceiptErrorCode
from ....inventory.exceptions import ReceiptNotInProgress
from ....inventory.models import Receipt as ReceiptModel
from ....inventory.receipt_workflow import update_receipt_lines
from ....permission.enums import WarehousePermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.utils import from_global_id_or_error
from ..types import Receipt, ReceiptError


class ReceiptLineInput(graphene.InputObjectType):
    purchase_order_item_id = graphene.ID(
        required=True,
        description="ID of the purchase order item.",
    )
    quantity = graphene.Int(
        required=True,
        description="Absolute quantity received. 0 removes the line.",
    )


class ReceiptUpdateLines(BaseMutation):
    """Set received quantities on a receipt by purchase order item."""

    receipt = graphene.Field(
        Receipt,
        description="The updated receipt.",
    )

    class Arguments:
        receipt_id = graphene.ID(
            required=True,
            description="ID of the receipt.",
        )
        lines = graphene.List(
            graphene.NonNull(ReceiptLineInput),
            required=True,
            description="Lines to upsert.",
        )

    class Meta:
        description = "Set received quantities on a receipt. Creates, updates, or removes receipt lines as needed."
        permissions = (WarehousePermissions.MANAGE_STOCK,)
        error_type_class = ReceiptError
        error_type_field = "receipt_errors"
        doc_category = DOC_CATEGORY_PRODUCTS

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        receipt_id = data["receipt_id"]
        lines = data["lines"]

        if not lines:
            raise ValidationError(
                {
                    "lines": ValidationError(
                        "At least one line is required.",
                        code=ReceiptErrorCode.INVALID.value,
                    )
                }
            )

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

        resolved_lines = []
        for i, line in enumerate(lines):
            _, poi_pk = from_global_id_or_error(
                line["purchase_order_item_id"], "PurchaseOrderItem"
            )
            quantity = line["quantity"]

            if quantity < 0:
                raise ValidationError(
                    {
                        "lines": ValidationError(
                            f"Quantity cannot be negative at index {i}.",
                            code=ReceiptErrorCode.INVALID.value,
                        )
                    }
                )

            resolved_lines.append(
                {"purchase_order_item_id": poi_pk, "quantity": quantity}
            )

        try:
            update_receipt_lines(
                receipt=receipt,
                lines_data=resolved_lines,
                user=info.context.user,
            )
        except ReceiptNotInProgress as e:
            raise ValidationError(
                {
                    "receipt_id": ValidationError(
                        str(e),
                        code=ReceiptErrorCode.INVALID.value,
                    )
                }
            ) from e

        receipt.refresh_from_db()
        return ReceiptUpdateLines(receipt=receipt)
