import graphene
from django.core.exceptions import ValidationError

from ....inventory.error_codes import ReceiptErrorCode
from ....inventory.models import Receipt as ReceiptModel
from ....inventory.receipt_workflow import resolve_product_discrepancy
from ....permission.enums import WarehousePermissions
from ....product.models import Product
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType, NonNullList
from ...core.utils import from_global_id_or_error
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import PurchaseOrderItemAdjustment, ReceiptError


class OrderResolutionInput(BaseInputObjectType):
    order_id = graphene.ID(
        required=True,
        description="ID of the order to allocate to.",
    )
    variant_id = graphene.ID(
        required=True,
        description="ID of the product variant to allocate.",
    )
    quantity = graphene.Int(
        required=True,
        description="Quantity to allocate.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ResolveProductDiscrepancy(BaseMutation):
    """Resolve all pending POIAs for a product on a receipt."""

    adjustments = graphene.List(
        graphene.NonNull(PurchaseOrderItemAdjustment),
        description="The resolved adjustments.",
        required=True,
    )

    class Arguments:
        receipt_id = graphene.ID(
            required=True,
            description="ID of the completed receipt.",
        )
        product_id = graphene.ID(
            required=True,
            description="ID of the product to resolve.",
        )
        resolutions = NonNullList(
            OrderResolutionInput,
            required=True,
            description=(
                "Desired allocation end-state. Each entry specifies an order, "
                "variant, and quantity. Omitted (order, variant) pairs are removed."
            ),
        )
        affects_payable = graphene.Boolean(
            required=True,
            description="Whether the supplier owes credit for this discrepancy.",
        )

    class Meta:
        description = (
            "Resolve pending purchase order item adjustments for a product. "
            "Allows removing allocations (shorting orders) or substituting "
            "variants. Marks all pending POIAs as processed."
        )
        permissions = (WarehousePermissions.MANAGE_STOCK,)
        error_type_class = ReceiptError
        error_type_field = "receipt_errors"
        doc_category = DOC_CATEGORY_PRODUCTS

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        from ....order.models import Order

        receipt_id = data["receipt_id"]
        product_id = data["product_id"]
        raw_resolutions = data["resolutions"]
        affects_payable = data["affects_payable"]

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

        resolutions = []
        for r in raw_resolutions:
            _, order_pk = from_global_id_or_error(r["order_id"], "Order")
            _, variant_pk = from_global_id_or_error(r["variant_id"], "ProductVariant")
            try:
                order = Order.objects.get(pk=order_pk)
            except Order.DoesNotExist:
                raise ValidationError(
                    {
                        "resolutions": ValidationError(
                            f"Order {r['order_id']} not found.",
                            code=ReceiptErrorCode.NOT_FOUND.value,
                        )
                    }
                ) from None

            from ....product.models import ProductVariant

            try:
                variant = ProductVariant.objects.get(pk=variant_pk)
            except ProductVariant.DoesNotExist:
                raise ValidationError(
                    {
                        "resolutions": ValidationError(
                            f"Variant {r['variant_id']} not found.",
                            code=ReceiptErrorCode.NOT_FOUND.value,
                        )
                    }
                ) from None

            resolutions.append(
                {
                    "order": order,
                    "variant": variant,
                    "quantity": r["quantity"],
                }
            )

        manager = get_plugin_manager_promise(info.context).get()

        try:
            adjustments = resolve_product_discrepancy(
                receipt=receipt,
                product=product,
                resolutions=resolutions,
                affects_payable=affects_payable,
                user=info.context.user,
                manager=manager,
            )
        except ValueError as e:
            raise ValidationError(
                {
                    "resolutions": ValidationError(
                        str(e),
                        code=ReceiptErrorCode.INVALID.value,
                    )
                }
            ) from e

        return ResolveProductDiscrepancy(adjustments=adjustments)
