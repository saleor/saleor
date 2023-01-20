from typing import Dict, cast

import graphene
from django.core.exceptions import ValidationError

from ...account.models import User
from ...core import JobStatus
from ...invoice import events, models
from ...invoice.error_codes import InvoiceErrorCode
from ...invoice.notifications import send_invoice
from ...order import events as order_events
from ...permission.enums import OrderPermissions
from ..app.dataloaders import get_app_promise
from ..core import ResolveInfo
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.types import InvoiceError
from ..order.types import Order
from ..plugins.dataloaders import get_plugin_manager_promise
from .types import Invoice
from .utils import is_event_active_for_any_plugin


class InvoiceRequest(ModelMutation):
    order = graphene.Field(Order, description="Order related to an invoice.")

    class Meta:
        description = "Request an invoice for the order using plugin."
        model = models.Invoice
        object_type = Invoice
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"

    class Arguments:
        order_id = graphene.ID(
            required=True, description="ID of the order related to invoice."
        )
        number = graphene.String(
            required=False,
            description="Invoice number, if not provided it will be generated.",
        )

    @staticmethod
    def clean_order(order):
        if order.is_draft() or order.is_unconfirmed():
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        "Cannot request an invoice for draft or unconfirmed order.",
                        code=InvoiceErrorCode.INVALID_STATUS.value,
                    )
                }
            )

        if not order.billing_address:
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        "Cannot request an invoice for order without billing address.",
                        code=InvoiceErrorCode.NOT_READY.value,
                    )
                }
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, number=None, order_id
    ):
        order = cls.get_node_or_error(info, order_id, only_type=Order, field="orderId")
        cls.clean_order(order)
        manager = get_plugin_manager_promise(info.context).get()
        if not is_event_active_for_any_plugin("invoice_request", manager.all_plugins):
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        "No app or plugin is configured to handle invoice requests.",
                        code=InvoiceErrorCode.NO_INVOICE_PLUGIN.value,
                    )
                }
            )

        shallow_invoice = models.Invoice.objects.create(
            order=order,
            number=number,
        )

        invoice = manager.invoice_request(
            order=order, invoice=shallow_invoice, number=number
        )
        app = get_app_promise(info.context).get()
        if invoice and invoice.status == JobStatus.SUCCESS:
            order_events.invoice_generated_event(
                order=order,
                user=info.context.user,
                app=app,
                invoice_number=invoice.number,
            )
        else:
            order_events.invoice_requested_event(
                user=info.context.user, app=app, order=order
            )

        events.invoice_requested_event(
            user=info.context.user,
            app=app,
            order=order,
            number=number,
        )
        return InvoiceRequest(invoice=invoice, order=order)


class InvoiceCreateInput(graphene.InputObjectType):
    number = graphene.String(required=True, description="Invoice number.")
    url = graphene.String(required=True, description="URL of an invoice to download.")


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
        if order.is_draft() or order.is_unconfirmed():
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        "Cannot create an invoice for draft or unconfirmed order.",
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
        cls.clean_order(info, order)
        cleaned_input = cls.clean_input(info, order, input)
        invoice = models.Invoice(**cleaned_input)
        invoice.order = order
        invoice.status = JobStatus.SUCCESS
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


class InvoiceRequestDelete(ModelMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="ID of an invoice to request the deletion."
        )

    class Meta:
        description = "Requests deletion of an invoice."
        model = models.Invoice
        object_type = Invoice
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id
    ):
        invoice = cls.get_node_or_error(info, id, only_type=Invoice)
        invoice.status = JobStatus.PENDING
        invoice.save(update_fields=["status", "updated_at"])
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.invoice_delete, invoice)
        app = get_app_promise(info.context).get()
        events.invoice_requested_deletion_event(
            user=info.context.user, app=app, invoice=invoice
        )
        return InvoiceRequestDelete(invoice=invoice)


class InvoiceDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an invoice to delete.")

    class Meta:
        description = "Deletes an invoice."
        model = models.Invoice
        object_type = Invoice
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        invoice = cls.get_instance(info, **data)
        response = super().perform_mutation(_root, info, **data)
        app = get_app_promise(info.context).get()
        events.invoice_deleted_event(
            user=info.context.user, app=app, invoice_id=invoice.pk
        )
        return response


class UpdateInvoiceInput(graphene.InputObjectType):
    number = graphene.String(description="Invoice number")
    url = graphene.String(description="URL of an invoice to download.")


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

    @classmethod
    def clean_input(cls, _info: ResolveInfo, instance, data):  # type: ignore[override]
        number = instance.number or data.get("number")
        url = instance.external_url or data.get("url")

        validation_errors: Dict[str, ValidationError] = {}
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
        cleaned_input = cls.clean_input(info, instance, input)
        instance.update_invoice(
            number=cleaned_input.get("number"), url=cleaned_input.get("url")
        )
        instance.status = JobStatus.SUCCESS
        instance.save(update_fields=["external_url", "number", "updated_at", "status"])
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


class InvoiceSendNotification(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an invoice to be sent.")

    class Meta:
        description = "Send an invoice notification to the customer."
        model = models.Invoice
        object_type = Invoice
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"

    @classmethod
    def clean_instance(cls, _info: ResolveInfo, instance):
        validation_errors = {}
        if instance.status != JobStatus.SUCCESS:
            validation_errors["invoice"] = ValidationError(
                "Provided invoice is not ready to be sent.",
                code=InvoiceErrorCode.NOT_READY.value,
            )
        if not instance.url:
            validation_errors["url"] = ValidationError(
                "Provided invoice needs to have an URL.",
                code=InvoiceErrorCode.URL_NOT_SET.value,
            )
        if not instance.number:
            validation_errors["number"] = ValidationError(
                "Provided invoice needs to have an invoice number.",
                code=InvoiceErrorCode.NUMBER_NOT_SET.value,
            )
        if not instance.order.get_customer_email():
            validation_errors["order"] = ValidationError(
                "Provided invoice order needs an email address.",
                code=InvoiceErrorCode.EMAIL_NOT_SET.value,
            )

        if validation_errors:
            raise ValidationError(validation_errors)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id
    ):
        user = info.context.user
        user = cast(User, user)
        instance = cls.get_instance(info, id=id)
        cls.clean_instance(info, instance)
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        send_invoice(
            invoice=instance,
            staff_user=user,
            app=app,
            manager=manager,
        )
        return InvoiceSendNotification(invoice=instance)
