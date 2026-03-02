import graphene
from django.core.exceptions import ValidationError
from django_countries import countries

from ....inventory import PurchaseOrderStatus, models
from ....inventory.error_codes import PurchaseOrderErrorCode
from ....permission.enums import WarehousePermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal
from ...core.utils import from_global_id_or_error
from ..types import PurchaseOrder, PurchaseOrderError


class UpdatePurchaseOrderItem(BaseMutation):
    purchase_order = graphene.Field(
        PurchaseOrder, description="The parent purchase order."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of the purchase order item.")
        quantity_ordered = graphene.Int(description="New quantity ordered.")
        unit_price_amount = PositiveDecimal(description="New unit cost (buy price).")
        currency = graphene.String(description="Currency code (e.g., GBP, USD).")
        country_of_origin = graphene.String(description="ISO 2-letter country code.")

    class Meta:
        description = "Updates an item on a draft purchase order."
        permissions = (WarehousePermissions.MANAGE_PURCHASE_ORDERS,)
        error_type_class = PurchaseOrderError
        error_type_field = "purchase_order_errors"
        doc_category = DOC_CATEGORY_PRODUCTS

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        _, pk = from_global_id_or_error(data["id"], "PurchaseOrderItem")

        try:
            poi = models.PurchaseOrderItem.objects.select_related("order").get(pk=pk)
        except models.PurchaseOrderItem.DoesNotExist:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Purchase order item not found.",
                        code=PurchaseOrderErrorCode.NOT_FOUND.value,
                    )
                }
            ) from None

        if poi.order.status != PurchaseOrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Only items on draft purchase orders can be updated.",
                        code=PurchaseOrderErrorCode.INVALID.value,
                    )
                }
            )

        update_fields = ["updated_at"]
        old_quantity = poi.quantity_ordered

        quantity = data.get("quantity_ordered")
        if quantity is not None:
            if quantity <= 0:
                raise ValidationError(
                    {
                        "quantity_ordered": ValidationError(
                            "Quantity must be greater than 0.",
                            code=PurchaseOrderErrorCode.INVALID_QUANTITY.value,
                        )
                    }
                )
            poi.quantity_ordered = quantity
            update_fields.append("quantity_ordered")

        unit_price = data.get("unit_price_amount")
        currency = data.get("currency")

        if unit_price is not None:
            if unit_price <= 0:
                raise ValidationError(
                    {
                        "unit_price_amount": ValidationError(
                            "Unit price must be greater than 0.",
                            code=PurchaseOrderErrorCode.INVALID_PRICE.value,
                        )
                    }
                )

        if currency is not None:
            if not (len(currency) == 3 and currency.isalpha()):
                raise ValidationError(
                    {
                        "currency": ValidationError(
                            "Currency must be a valid 3-letter code.",
                            code=PurchaseOrderErrorCode.INVALID_CURRENCY.value,
                        )
                    }
                )
            poi.currency = currency.upper()
            update_fields.append("currency")

        # If unit_price provided without currency, infer from PO, then existing POI, then siblings
        if unit_price is not None and currency is None and not poi.currency:
            po_currency = poi.order.currency
            if po_currency:
                poi.currency = po_currency
                update_fields.append("currency")
            else:
                sibling_currency = (
                    models.PurchaseOrderItem.objects.filter(order=poi.order)
                    .exclude(currency__isnull=True)
                    .exclude(currency="")
                    .values_list("currency", flat=True)
                    .first()
                )
                if sibling_currency:
                    poi.currency = sibling_currency
                    update_fields.append("currency")

        # Recalculate total_price if unit_price or quantity changed
        if unit_price is not None:
            q = quantity if quantity is not None else poi.quantity_ordered
            poi.total_price_amount = unit_price * q
            update_fields.append("total_price_amount")
        elif (
            quantity is not None
            and poi.total_price_amount is not None
            and old_quantity > 0
        ):
            # quantity changed but price didn't — recalculate total from existing unit price
            old_unit = poi.total_price_amount / old_quantity
            poi.total_price_amount = old_unit * quantity
            update_fields.append("total_price_amount")

        country_of_origin = data.get("country_of_origin")
        if country_of_origin is not None:
            if country_of_origin == "":
                poi.country_of_origin = None
            elif country_of_origin.upper() not in dict(countries):
                raise ValidationError(
                    {
                        "country_of_origin": ValidationError(
                            "Invalid country code.",
                            code=PurchaseOrderErrorCode.INVALID_COUNTRY.value,
                        )
                    }
                )
            else:
                poi.country_of_origin = country_of_origin.upper()
            update_fields.append("country_of_origin")

        poi.save(update_fields=update_fields)

        return UpdatePurchaseOrderItem(purchase_order=poi.order)
