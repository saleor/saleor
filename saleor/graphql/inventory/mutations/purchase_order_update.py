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


class PurchaseOrderUpdate(BaseMutation):
    purchase_order = graphene.Field(
        PurchaseOrder, description="The updated purchase order."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of the purchase order.")
        name = graphene.String(description="New name for the purchase order.")
        currency = graphene.String(
            description="Default currency for the purchase order (3-letter code).",
        )
        auto_reallocate_variants = graphene.Boolean(
            description="Whether variants are automatically reallocated on receipt.",
        )

    class Meta:
        description = "Updates a draft purchase order."
        permissions = (WarehousePermissions.MANAGE_PURCHASE_ORDERS,)
        error_type_class = PurchaseOrderError
        error_type_field = "purchase_order_errors"
        doc_category = DOC_CATEGORY_PRODUCTS

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        _, pk = from_global_id_or_error(data["id"], "PurchaseOrder")

        try:
            purchase_order = models.PurchaseOrder.objects.get(pk=pk)
        except models.PurchaseOrder.DoesNotExist:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Purchase order not found.",
                        code=PurchaseOrderErrorCode.NOT_FOUND.value,
                    )
                }
            ) from None

        if purchase_order.status != PurchaseOrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Only draft purchase orders can be updated.",
                        code=PurchaseOrderErrorCode.INVALID.value,
                    )
                }
            )

        update_fields = ["updated_at"]
        if "name" in data and data["name"] is not None:
            purchase_order.name = data["name"]
            update_fields.append("name")
        currency = data.get("currency")
        if currency is not None:
            if not (len(currency) == 3 and currency.isalpha()):
                raise ValidationError(
                    {
                        "currency": ValidationError(
                            "Currency must be a valid 3-letter code.",
                            code=PurchaseOrderErrorCode.INVALID.value,
                        )
                    }
                )
            purchase_order.currency = currency.upper()
            update_fields.append("currency")
            # Propagate to all items that don't have a currency yet
            models.PurchaseOrderItem.objects.filter(
                order=purchase_order,
            ).filter(models.Q(currency__isnull=True) | models.Q(currency="")).update(
                currency=currency.upper()
            )
        if (
            "auto_reallocate_variants" in data
            and data["auto_reallocate_variants"] is not None
        ):
            purchase_order.auto_reallocate_variants = data["auto_reallocate_variants"]
            update_fields.append("auto_reallocate_variants")

        purchase_order.save(update_fields=update_fields)

        return PurchaseOrderUpdate(purchase_order=purchase_order)
