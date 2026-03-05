import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

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
from ..types import Receipt, ReceiptError


class ReceiveItemInput(graphene.InputObjectType):
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


class ReceiptReceiveItemsBatch(BaseMutation):
    """Record receiving multiple items in a single batch."""

    receipt = graphene.Field(
        Receipt,
        description="The updated receipt.",
    )

    class Arguments:
        receipt_id = graphene.ID(
            required=True,
            description="ID of the receipt to add items to.",
        )
        items = graphene.List(
            graphene.NonNull(ReceiveItemInput),
            required=True,
            description="List of items to receive.",
        )

    class Meta:
        description = "Record receiving multiple items in a single batch operation."
        permissions = (WarehousePermissions.MANAGE_STOCK,)
        error_type_class = ReceiptError
        error_type_field = "receipt_errors"
        doc_category = DOC_CATEGORY_PRODUCTS

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        receipt_id = data["receipt_id"]
        items = data["items"]

        if not items:
            raise ValidationError(
                {
                    "items": ValidationError(
                        "At least one item is required.",
                        code=ReceiptErrorCode.INVALID.value,
                    )
                }
            )

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

        # Resolve all variants upfront
        resolved_items = []
        for i, item in enumerate(items):
            variant_id = item["variant_id"]
            quantity = item["quantity"]
            notes = item.get("notes", "")

            _, variant_pk = from_global_id_or_error(variant_id, "ProductVariant")
            try:
                variant = ProductVariant.objects.get(pk=variant_pk)
            except ProductVariant.DoesNotExist:
                raise ValidationError(
                    {
                        "items": ValidationError(
                            f"Product variant not found at index {i}.",
                            code=ReceiptErrorCode.NOT_FOUND.value,
                        )
                    }
                ) from None

            if quantity <= 0:
                raise ValidationError(
                    {
                        "items": ValidationError(
                            f"Quantity must be positive at index {i}.",
                            code=ReceiptErrorCode.INVALID.value,
                        )
                    }
                )

            resolved_items.append((variant, quantity, notes))

        # Execute all receive_item calls in a single transaction
        try:
            with transaction.atomic():
                for variant, quantity, notes in resolved_items:
                    receive_item(
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
                    "items": ValidationError(
                        str(e),
                        code=ReceiptErrorCode.INVALID.value,
                    )
                }
            ) from e

        # Refresh receipt to get updated lines
        receipt.refresh_from_db()
        return ReceiptReceiveItemsBatch(receipt=receipt)
