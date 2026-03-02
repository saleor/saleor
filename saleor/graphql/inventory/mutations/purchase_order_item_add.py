import graphene
from django.core.exceptions import ValidationError
from django_countries import countries

from ....inventory import PurchaseOrderItemStatus, PurchaseOrderStatus, models
from ....inventory.error_codes import PurchaseOrderErrorCode
from ....permission.enums import WarehousePermissions
from ....product.models import ProductVariant
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal
from ...core.utils import from_global_id_or_error
from ..types import PurchaseOrder, PurchaseOrderError


class AddPurchaseOrderItem(BaseMutation):
    purchase_order = graphene.Field(
        PurchaseOrder, description="The updated purchase order."
    )

    class Arguments:
        purchase_order_id = graphene.ID(
            required=True, description="ID of the draft purchase order."
        )
        variant_id = graphene.ID(required=True, description="Product variant to add.")
        quantity_ordered = graphene.Int(required=True, description="Quantity to order.")
        unit_price_amount = PositiveDecimal(description="Unit cost (buy price).")
        currency = graphene.String(description="Currency code (e.g., GBP, USD).")
        country_of_origin = graphene.String(description="ISO 2-letter country code.")

    class Meta:
        description = "Adds an item to a draft purchase order."
        permissions = (WarehousePermissions.MANAGE_PURCHASE_ORDERS,)
        error_type_class = PurchaseOrderError
        error_type_field = "purchase_order_errors"
        doc_category = DOC_CATEGORY_PRODUCTS

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        _, po_pk = from_global_id_or_error(data["purchase_order_id"], "PurchaseOrder")
        _, variant_pk = from_global_id_or_error(data["variant_id"], "ProductVariant")

        try:
            purchase_order = models.PurchaseOrder.objects.get(pk=po_pk)
        except models.PurchaseOrder.DoesNotExist:
            raise ValidationError(
                {
                    "purchase_order_id": ValidationError(
                        "Purchase order not found.",
                        code=PurchaseOrderErrorCode.NOT_FOUND.value,
                    )
                }
            ) from None

        if purchase_order.status != PurchaseOrderStatus.DRAFT:
            raise ValidationError(
                {
                    "purchase_order_id": ValidationError(
                        "Only draft purchase orders can be modified.",
                        code=PurchaseOrderErrorCode.INVALID.value,
                    )
                }
            )

        try:
            variant = ProductVariant.objects.get(pk=variant_pk)
        except ProductVariant.DoesNotExist:
            raise ValidationError(
                {
                    "variant_id": ValidationError(
                        "Product variant not found.",
                        code=PurchaseOrderErrorCode.INVALID_VARIANT.value,
                    )
                }
            ) from None

        quantity = data["quantity_ordered"]
        if quantity <= 0:
            raise ValidationError(
                {
                    "quantity_ordered": ValidationError(
                        "Quantity must be greater than 0.",
                        code=PurchaseOrderErrorCode.INVALID_QUANTITY.value,
                    )
                }
            )

        unit_price = data.get("unit_price_amount")
        currency = data.get("currency")
        country_of_origin = data.get("country_of_origin")

        if unit_price is not None and unit_price <= 0:
            raise ValidationError(
                {
                    "unit_price_amount": ValidationError(
                        "Unit price must be greater than 0.",
                        code=PurchaseOrderErrorCode.INVALID_PRICE.value,
                    )
                }
            )

        if currency and not (len(currency) == 3 and currency.isalpha()):
            raise ValidationError(
                {
                    "currency": ValidationError(
                        "Currency must be a valid 3-letter code.",
                        code=PurchaseOrderErrorCode.INVALID_CURRENCY.value,
                    )
                }
            )

        if country_of_origin and country_of_origin.upper() not in dict(countries):
            raise ValidationError(
                {
                    "country_of_origin": ValidationError(
                        "Invalid country code.",
                        code=PurchaseOrderErrorCode.INVALID_COUNTRY.value,
                    )
                }
            )

        total_price = unit_price * quantity if unit_price is not None else None

        models.PurchaseOrderItem.objects.create(
            order=purchase_order,
            product_variant=variant,
            quantity_ordered=quantity,
            total_price_amount=total_price,
            currency=currency.upper() if currency else None,
            country_of_origin=country_of_origin.upper() if country_of_origin else None,
            status=PurchaseOrderItemStatus.DRAFT,
        )

        return AddPurchaseOrderItem(purchase_order=purchase_order)
