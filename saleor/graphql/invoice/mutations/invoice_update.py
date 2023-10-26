import graphene
from django.core.exceptions import ValidationError

from ....core import JobStatus
from ....invoice import models
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
from ..types import Invoice


class UpdateInvoiceInput(BaseInputObjectType):
    number = graphene.String(description="Invoice number")
    url = graphene.String(description="URL of an invoice to download.")
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


class InvoiceUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an invoice to update.")
        input = UpdateInvoiceInput(
            required=True, description="Fields to use when updating an invoice."
        )

    class Meta:
        description = "Updates an invoice."
        model = models.Invoice
        object_type = Invoice
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def clean_input(cls, _info: ResolveInfo, instance, data):  # type: ignore[override]
        number = instance.number or data.get("number")
        url = instance.external_url or data.get("url")

        validation_errors: dict[str, ValidationError] = {}
        if not number:
            validation_errors["number"] = ValidationError(
                "Number need to be set after update operation.",
                code=InvoiceErrorCode.NUMBER_NOT_SET.value,
            )
        if not url:
            validation_errors["url"] = ValidationError(
                "URL need to be set after update operation.",
                code=InvoiceErrorCode.URL_NOT_SET.value,
            )

        if validation_errors:
            raise ValidationError(validation_errors)

        return data

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        instance = cls.get_instance(info, id=id)
        cls.check_channel_permissions(info, [instance.order.channel_id])
        cleaned_input = cls.clean_input(info, instance, input)
        metadata_list = cleaned_input.pop("metadata", None)
        private_metadata_list = cleaned_input.pop("private_metadata", None)
        cls.validate_and_update_metadata(instance, metadata_list, private_metadata_list)
        instance.update_invoice(
            number=cleaned_input.get("number"), url=cleaned_input.get("url")
        )
        instance.status = JobStatus.SUCCESS
        instance.save(
            update_fields=[
                "external_url",
                "number",
                "updated_at",
                "status",
                "metadata",
                "private_metadata",
            ]
        )
        app = get_app_promise(info.context).get()
        order_events.invoice_updated_event(
            order=instance.order,
            user=info.context.user,
            app=app,
            invoice_number=instance.number,
            url=instance.url,
            status=instance.status,
        )
        return InvoiceUpdate(invoice=instance)
