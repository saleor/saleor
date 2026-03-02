import graphene
from django.core.exceptions import ValidationError

from ....inventory.error_codes import ReceiptErrorCode
from ....inventory.exceptions import ReceiptNotInProgress
from ....inventory.models import Receipt as ReceiptModel
from ....inventory.receipt_workflow import receive_item
from ....permission.enums import WarehousePermissions
from ....product.models import ProductVariant
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.utils import from_global_id_or_error
from ..types import ReceiptError, ReceiptLine


class ReceiptReceiveItem(BaseMutation):
    """Add a received item to a receipt."""

    receipt_line = graphene.Field(
        ReceiptLine,
        description="The created receipt line.",
    )

    class Arguments:
        receipt_id = graphene.ID(
            required=True,
            description="ID of the receipt to add items to.",
        )
        variant_id = graphene.ID(
            required=True,
            description="ID of the product variant being received.",
        )
        quantity = graphene.Int(
            required=True,
            description="Quantity received.",
        )
        notes = graphene.String(
            description="Optional notes about this item.",
        )

    class Meta:
        description = "Record receiving an item during a receipt."
        permissions = (WarehousePermissions.MANAGE_STOCK,)
        error_type_class = ReceiptError
        error_type_field = "receipt_errors"
        doc_category = DOC_CATEGORY_PRODUCTS

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        receipt_id = data["receipt_id"]
        variant_id = data["variant_id"]
        quantity = data["quantity"]
        notes = data.get("notes", "")

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

        # Get variant
        _, variant_pk = from_global_id_or_error(variant_id, "ProductVariant")
        try:
            variant = ProductVariant.objects.get(pk=variant_pk)
        except ProductVariant.DoesNotExist:
            raise ValidationError(
                {
                    "variant_id": ValidationError(
                        "Product variant not found.",
                        code=ReceiptErrorCode.NOT_FOUND.value,
                    )
                }
            ) from None

        # Validate quantity
        if quantity <= 0:
            raise ValidationError(
                {
                    "quantity": ValidationError(
                        "Quantity must be positive.",
                        code=ReceiptErrorCode.INVALID.value,
                    )
                }
            )

        # Receive item
        try:
            receipt_line = receive_item(
                receipt=receipt,
                product_variant=variant,
                quantity=quantity,
                user=info.context.user,
                notes=notes,
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
        except ValueError as e:
            raise ValidationError(
                {
                    "variant_id": ValidationError(
                        str(e),
                        code=ReceiptErrorCode.INVALID.value,
                    )
                }
            ) from e

        return ReceiptReceiveItem(receipt_line=receipt_line)
