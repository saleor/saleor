import graphene
from django.core.exceptions import ValidationError

from ....inventory.error_codes import ReceiptErrorCode
from ....inventory.receipt_workflow import start_receipt
from ....permission.enums import WarehousePermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.utils import from_global_id_or_error
from ..types import Receipt, ReceiptError


class ReceiptStart(BaseMutation):
    """Start a new receipt for an inbound shipment."""

    receipt = graphene.Field(
        Receipt,
        description="The created receipt.",
    )

    class Arguments:
        shipment_id = graphene.ID(
            required=True,
            description="ID of the shipment to receive.",
        )

    class Meta:
        description = "Start receiving goods from an inbound shipment."
        permissions = (WarehousePermissions.MANAGE_STOCK,)
        error_type_class = ReceiptError
        error_type_field = "receipt_errors"
        doc_category = DOC_CATEGORY_PRODUCTS

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        shipment_id = data["shipment_id"]

        # Get shipment
        _, shipment_pk = from_global_id_or_error(shipment_id, "Shipment")

        from ....shipping.models import Shipment as ShipmentModel

        try:
            shipment = ShipmentModel.objects.get(pk=shipment_pk)
        except ShipmentModel.DoesNotExist:
            raise ValidationError(
                {
                    "shipment_id": ValidationError(
                        "Shipment not found.",
                        code=ReceiptErrorCode.NOT_FOUND.value,
                    )
                }
            ) from None

        # Start receipt
        try:
            receipt = start_receipt(shipment, user=info.context.user)
        except ValueError as e:
            raise ValidationError(
                {
                    "shipment_id": ValidationError(
                        str(e),
                        code=ReceiptErrorCode.INVALID.value,
                    )
                }
            ) from e

        return ReceiptStart(receipt=receipt)
