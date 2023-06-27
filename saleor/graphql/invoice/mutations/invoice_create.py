import graphene
from django.core.exceptions import ValidationError

from ....core import JobStatus
from ....invoice import events, models
from ....invoice.error_codes import InvoiceErrorCode
from ....order import events as order_events
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_314
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import ModelMutation
from ...core.types import BaseInputObjectType, InvoiceError, NonNullList
from ...meta.inputs import MetadataInput
from ...order.types import Order
from ..types import Invoice


class InvoiceCreateInput(BaseInputObjectType):
    number = graphene.String(required=True, description="Invoice number.")
    url = graphene.String(required=True, description="URL of an invoice to download.")
    metadata = NonNullList(
        MetadataInput,
        description="Fields required to update the invoice metadata." + ADDED_IN_314,
        required=False,
    )
    private_metadata = NonNullList(
        MetadataInput,
        description=(
            "Fields required to update the invoice private metadata." + ADDED_IN_314
        ),
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class InvoiceCreate(ModelMutation):
    class Arguments:
        order_id = graphene.ID(
            required=True, description="ID of the order related to invoice."
        )
        input = InvoiceCreateInput(
            required=True, description="Fields required when creating an invoice."
        )

    class Meta:
        description = "Creates a ready to send invoice."
        model = models.Invoice
        object_type = Invoice
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def clean_input(cls, _info: ResolveInfo, _instance, data):  # type: ignore[override]
        validation_errors = {}
        for field in ["url", "number"]:
            if data[field] == "":
                validation_errors[field] = ValidationError(
                    f"{field} cannot be empty.",
                    code=InvoiceErrorCode.REQUIRED.value,
                )
        if validation_errors:
            raise ValidationError(validation_errors)
        return data

    @classmethod
    def clean_order(cls, info: ResolveInfo, order):
        if order.is_draft() or order.is_unconfirmed() or order.is_expired():
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        "Cannot create an invoice for draft, "
                        "unconfirmed or expired order.",
                        code=InvoiceErrorCode.INVALID_STATUS.value,
                    )
                }
            )

        if not order.billing_address:
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        "Cannot create an invoice for order without billing address.",
                        code=InvoiceErrorCode.NOT_READY.value,
                    )
                }
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input, order_id
    ):
        order = cls.get_node_or_error(info, order_id, only_type=Order, field="orderId")
        cls.check_channel_permissions(info, [order.channel_id])
        cls.clean_order(info, order)
        cleaned_input = cls.clean_input(info, order, input)

        metadata_list = cleaned_input.pop("metadata", None)
        private_metadata_list = cleaned_input.pop("private_metadata", None)

        invoice = models.Invoice(**cleaned_input)
        invoice.order = order
        invoice.status = JobStatus.SUCCESS
        cls.validate_and_update_metadata(invoice, metadata_list, private_metadata_list)
        invoice.save()

        app = get_app_promise(info.context).get()
        events.invoice_created_event(
            user=info.context.user,
            app=app,
            invoice=invoice,
            number=cleaned_input["number"],
            url=cleaned_input["url"],
        )
        order_events.invoice_generated_event(
            order=order,
            user=info.context.user,
            app=app,
            invoice_number=cleaned_input["number"],
        )
        return InvoiceCreate(invoice=invoice)
