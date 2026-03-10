import graphene
from django.core.exceptions import ValidationError

from ....inventory.error_codes import ReceiptErrorCode
from ....inventory.exceptions import ReceiptNotInProgress
from ....inventory.models import Receipt as ReceiptModel
from ....inventory.receipt_workflow import update_receipt_lines
from ....permission.enums import WarehousePermissions
from ....product.models import Product, ProductVariant
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.utils import from_global_id_or_error
from ..types import Receipt, ReceiptError


class ReceiptLineInput(graphene.InputObjectType):
    purchase_order_item_id = graphene.ID(
        required=False,
        description=(
            "ID of the purchase order item. "
            "Exactly one of purchaseOrderItemId or variantId must be provided."
        ),
    )
    variant_id = graphene.ID(
        required=False,
        description=(
            "ID of an existing product variant. Use this to receive an "
            "unexpected variant — a POI will be auto-created if a sibling "
            "variant is on the shipment."
        ),
    )
    product_id = graphene.ID(
        required=False,
        description=(
            "ID of the product. Used together with variantName to receive a "
            "variant that doesn't exist yet — the variant will be created "
            "automatically (copying attributes and channel listings from a "
            "sibling)."
        ),
    )
    variant_name = graphene.String(
        required=False,
        description=(
            "Name of the variant to create (e.g. a size like 'XL'). "
            "Must be provided together with productId."
        ),
    )
    quantity = graphene.Int(
        required=True,
        description="Absolute quantity received. 0 removes the line.",
    )


class ReceiptUpdateLines(BaseMutation):
    """Set received quantities on a receipt by purchase order item or variant."""

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
            poi_gid = line.get("purchase_order_item_id")
            variant_gid = line.get("variant_id")
            product_gid = line.get("product_id")
            variant_name = line.get("variant_name")
            quantity = line["quantity"]

            has_poi = bool(poi_gid)
            has_variant = bool(variant_gid)
            has_new_variant = bool(product_gid) or bool(variant_name)

            identifiers = sum([has_poi, has_variant, has_new_variant])
            if identifiers != 1:
                raise ValidationError(
                    {
                        "lines": ValidationError(
                            f"Provide exactly one of: purchaseOrderItemId, "
                            f"variantId, or productId+variantName (index {i}).",
                            code=ReceiptErrorCode.INVALID.value,
                        )
                    }
                )

            if has_new_variant and (not product_gid or not variant_name):
                raise ValidationError(
                    {
                        "lines": ValidationError(
                            f"Both productId and variantName must be provided "
                            f"together (index {i}).",
                            code=ReceiptErrorCode.INVALID.value,
                        )
                    }
                )

            if quantity < 0:
                raise ValidationError(
                    {
                        "lines": ValidationError(
                            f"Quantity cannot be negative at index {i}.",
                            code=ReceiptErrorCode.INVALID.value,
                        )
                    }
                )

            entry: dict = {"quantity": quantity}
            if has_poi:
                _, poi_pk = from_global_id_or_error(poi_gid, "PurchaseOrderItem")
                entry["purchase_order_item_id"] = poi_pk
            elif has_variant:
                _, variant_pk = from_global_id_or_error(variant_gid, "ProductVariant")
                try:
                    entry["variant"] = ProductVariant.objects.get(pk=variant_pk)
                except ProductVariant.DoesNotExist:
                    raise ValidationError(
                        {
                            "lines": ValidationError(
                                f"Product variant not found (index {i}).",
                                code=ReceiptErrorCode.NOT_FOUND.value,
                            )
                        }
                    ) from None
            else:
                _, product_pk = from_global_id_or_error(product_gid, "Product")
                try:
                    entry["product"] = Product.objects.get(pk=product_pk)
                except Product.DoesNotExist:
                    raise ValidationError(
                        {
                            "lines": ValidationError(
                                f"Product not found (index {i}).",
                                code=ReceiptErrorCode.NOT_FOUND.value,
                            )
                        }
                    ) from None
                entry["variant_name"] = variant_name

            resolved_lines.append(entry)

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
        except ValueError as e:
            raise ValidationError(
                {
                    "lines": ValidationError(
                        str(e),
                        code=ReceiptErrorCode.INVALID.value,
                    )
                }
            ) from e

        receipt.refresh_from_db()
        return ReceiptUpdateLines(receipt=receipt)
