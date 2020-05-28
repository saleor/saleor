import graphene
from django.core.exceptions import ValidationError

from ...core.permissions import OrderPermissions
from ...invoice import events, models
from ...invoice.emails import send_invoice
from ...invoice.error_codes import InvoiceErrorCode
from ...order import OrderStatus
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.types.common import InvoiceError
from ..invoice.enums import InvoiceStatus
from ..invoice.types import InvoiceJob
from ..order.types import Order


class RequestInvoice(ModelMutation):
    class Meta:
        description = "Request an invoice for the order."
        model = models.InvoiceJob
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"

    class Arguments:
        order_id = graphene.ID(
            required=True, description="ID of the order related to invoice."
        )
        number = graphene.String(
            required=False, description="Invoice number (optional)."
        )

    @classmethod
    def clean_instance(cls, info, instance):
        if instance.status == OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        "Provided order status cannot be draft.",
                        code=InvoiceErrorCode.INVALID_STATUS,
                    )
                }
            )

        if not instance.billing_address:
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        "Billing address is not set on order.",
                        code=InvoiceErrorCode.NOT_READY,
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(
            info, data["order_id"], only_type=Order, field="orderId"
        )
        cls.clean_instance(info, order)

        invoice = models.Invoice.objects.create(order=order, number=data.get("number"))
        job = models.InvoiceJob.objects.create(invoice=invoice)

        info.context.plugins.invoice_request(
            order=order, invoice_job=job, number=data.get("number")
        )
        events.invoice_requested_event(
            user=info.context.user, order=order, number=data.get("number")
        )
        invoice.refresh_from_db()
        return RequestInvoice(invoiceJob=job)


class CreateInvoiceInput(graphene.InputObjectType):
    number = graphene.String(required=True, description="Invoice number")
    url = graphene.String(required=True, description="URL of an invoice to download.")


class CreateInvoice(ModelMutation):
    class Arguments:
        order_id = graphene.ID(
            required=True, description="ID of the order related to invoice."
        )
        input = CreateInvoiceInput(
            required=True, description="Fields required when creating an invoice."
        )

    class Meta:
        description = "Creates an invoice."
        model = models.InvoiceJob
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        validation_errors = {}
        for field in ["url", "number"]:
            if data["input"][field] == "":
                validation_errors[field] = ValidationError(
                    f"{field} cannot be empty.", code=InvoiceErrorCode.REQUIRED,
                )
        if validation_errors:
            raise ValidationError(validation_errors)
        return data["input"]

    @classmethod
    def clean_instance(cls, info, instance):
        if instance.status == OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        "Provided order status cannot be draft.",
                        code=InvoiceErrorCode.INVALID_STATUS,
                    )
                }
            )

        if not instance.billing_address:
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        "Billing address is not set on order.",
                        code=InvoiceErrorCode.NOT_READY,
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        instance = cls.get_node_or_error(
            info, data["order_id"], only_type=Order, field="orderId"
        )
        cls.clean_instance(info, instance)
        cleaned_input = cls.clean_input(info, instance, data)
        invoice = models.Invoice(**cleaned_input)
        invoice.order = instance
        invoice.save()
        job = models.InvoiceJob.objects.create(
            invoice=invoice, status=InvoiceStatus.READY
        )
        events.invoice_created_event(
            user=info.context.user,
            invoice=invoice,
            number=cleaned_input["number"],
            url=cleaned_input["url"],
        )
        return CreateInvoice(invoiceJob=job)


class RequestDeleteInvoice(ModelMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="ID of an invoice to request the deletion."
        )

    class Meta:
        description = "Requests deletion of an invoice."
        model = models.InvoiceJob
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        invoice_job = cls.get_node_or_error(info, data["id"], only_type=InvoiceJob)
        invoice_job.status = InvoiceStatus.PENDING_DELETE
        invoice_job.save()
        info.context.plugins.invoice_delete(invoice_job)
        events.invoice_requested_deletion(
            user=info.context.user, invoice=invoice_job.invoice
        )
        return RequestDeleteInvoice(invoiceJob=invoice_job)


class DeleteInvoice(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an invoice to delete.")

    class Meta:
        description = "Deletes an invoice."
        model = models.InvoiceJob
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        invoice_job = cls.get_instance(info, **data)
        response = super().perform_mutation(_root, info, **data)
        events.invoice_deleted_event(
            user=info.context.user, invoice_id=invoice_job.invoice.pk
        )
        return response


class UpdateInvoiceInput(graphene.InputObjectType):
    number = graphene.String(description="Invoice number")
    url = graphene.String(description="URL of an invoice to download.")


class UpdateInvoice(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an invoice to update.")
        input = UpdateInvoiceInput(
            required=True, description="Fields to use when updating an invoice."
        )

    class Meta:
        description = "Updates an invoice."
        model = models.InvoiceJob
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        number = instance.invoice.number or data["input"].get("number")
        url = instance.invoice.url or data["input"].get("url")
        if not number or not url:
            raise ValidationError(
                {
                    "invoice": ValidationError(
                        "URL and number need to be set after update operation.",
                        code=InvoiceErrorCode.URL_OR_NUMBER_NOT_SET,
                    )
                }
            )
        return data["input"]

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        instance = cls.get_instance(info, **data)
        cleaned_input = cls.clean_input(info, instance, data)
        instance.invoice.update_invoice(
            number=cleaned_input.get("number"), url=cleaned_input.get("url")
        )
        instance.status = InvoiceStatus.READY
        instance.save()
        return UpdateInvoice(invoiceJob=instance)


class SendInvoiceEmail(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an invoice to be sent.")

    class Meta:
        description = "Send an invoice by email."
        model = models.InvoiceJob
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"

    @classmethod
    def clean_instance(cls, info, instance):
        error_code = None

        if instance.status != InvoiceStatus.READY:
            error_code = InvoiceErrorCode.NOT_READY
        elif not instance.invoice.url or not instance.invoice.number:
            error_code = InvoiceErrorCode.URL_OR_NUMBER_NOT_SET

        if error_code:
            raise ValidationError(
                "Provided invoice is not ready to be sent.", code=error_code
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        instance = cls.get_instance(info, **data)
        cls.clean_instance(info, instance)
        send_invoice.delay(instance.pk)
        events.invoice_sent_event(user=info.context.user, invoice=instance.invoice)
        return SendInvoiceEmail(invoiceJob=instance)
