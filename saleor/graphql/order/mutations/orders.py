import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
from ....core.exceptions import InsufficientStock
from ....core.permissions import OrderPermissions
from ....core.taxes import TaxError, zero_taxed_money
from ....core.tracing import traced_atomic_transaction
from ....order import FulfillmentStatus, OrderLineData, OrderStatus, events, models
from ....order.actions import (
    cancel_order,
    clean_mark_order_as_paid,
    mark_order_as_paid,
    order_captured,
    order_confirmed,
    order_refunded,
    order_shipping_updated,
    order_voided,
)
from ....order.error_codes import OrderErrorCode
from ....order.utils import (
    add_variant_to_order,
    change_order_line_quantity,
    delete_order_line,
    get_valid_shipping_methods_for_order,
    recalculate_order,
    update_order_prices,
)
from ....payment import PaymentError, TransactionKind, gateway
from ....shipping import models as shipping_models
from ...account.types import AddressInput
from ...core.mutations import BaseMutation, ModelMutation
from ...core.scalars import PositiveDecimal
from ...core.types.common import OrderError
from ...core.utils import validate_required_string_field
from ...order.mutations.draft_orders import (
    DraftOrderCreate,
    OrderLineCreateInput,
    OrderLineInput,
)
from ...product.types import ProductVariant
from ...shipping.types import ShippingMethod
from ..types import Order, OrderEvent, OrderLine
from ..utils import (
    validate_product_is_published_in_channel,
    validate_variant_channel_listings,
)

ORDER_EDITABLE_STATUS = (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED)


def clean_order_update_shipping(order, method):
    if not order.shipping_address:
        raise ValidationError(
            {
                "order": ValidationError(
                    "Cannot choose a shipping method for an order without "
                    "the shipping address.",
                    code=OrderErrorCode.ORDER_NO_SHIPPING_ADDRESS,
                )
            }
        )

    valid_methods = get_valid_shipping_methods_for_order(order)
    if valid_methods is None or method.pk not in valid_methods.values_list(
        "id", flat=True
    ):
        raise ValidationError(
            {
                "shipping_method": ValidationError(
                    "Shipping method cannot be used with this order.",
                    code=OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE,
                )
            }
        )


def clean_order_cancel(order):
    if order and not order.can_cancel():
        raise ValidationError(
            {
                "order": ValidationError(
                    "This order can't be canceled.",
                    code=OrderErrorCode.CANNOT_CANCEL_ORDER,
                )
            }
        )


def clean_payment(payment):
    if not payment:
        raise ValidationError(
            {
                "payment": ValidationError(
                    "There's no payment associated with the order.",
                    code=OrderErrorCode.PAYMENT_MISSING,
                )
            }
        )


def clean_order_capture(payment):
    clean_payment(payment)
    if not payment.is_active:
        raise ValidationError(
            {
                "payment": ValidationError(
                    "Only pre-authorized payments can be captured",
                    code=OrderErrorCode.CAPTURE_INACTIVE_PAYMENT,
                )
            }
        )


def clean_void_payment(payment):
    """Check for payment errors."""
    clean_payment(payment)
    if not payment.is_active:
        raise ValidationError(
            {
                "payment": ValidationError(
                    "Only pre-authorized payments can be voided",
                    code=OrderErrorCode.VOID_INACTIVE_PAYMENT,
                )
            }
        )


def clean_refund_payment(payment):
    clean_payment(payment)
    if not payment.can_refund():
        raise ValidationError(
            {
                "payment": ValidationError(
                    "Payment cannot be refunded.",
                    code=OrderErrorCode.CANNOT_REFUND,
                )
            }
        )


def try_payment_action(order, user, app, payment, func, *args, **kwargs):
    try:
        result = func(*args, **kwargs)
        # provided order might alter it's total_paid.
        order.refresh_from_db()
        return result
    except (PaymentError, ValueError) as e:
        message = str(e)
        events.payment_failed_event(
            order=order, user=user, app=app, message=message, payment=payment
        )
        raise ValidationError(
            {"payment": ValidationError(message, code=OrderErrorCode.PAYMENT_ERROR)}
        )


class OrderUpdateInput(graphene.InputObjectType):
    billing_address = AddressInput(description="Billing address of the customer.")
    user_email = graphene.String(description="Email address of the customer.")
    shipping_address = AddressInput(description="Shipping address of the customer.")


class OrderUpdate(DraftOrderCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an order to update.")
        input = OrderUpdateInput(
            required=True, description="Fields required to update an order."
        )

    class Meta:
        description = "Updates an order."
        model = models.Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        draft_order_cleaned_input = super().clean_input(info, instance, data)

        # We must to filter out field added by DraftOrderUpdate
        editable_fields = ["billing_address", "shipping_address", "user_email"]
        cleaned_input = {}
        for key in draft_order_cleaned_input:
            if key in editable_fields:
                cleaned_input[key] = draft_order_cleaned_input[key]
        return cleaned_input

    @classmethod
    def get_instance(cls, info, **data):
        instance = super().get_instance(info, **data)
        if instance.status == OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to draft order. "
                        "Use `draftOrderUpdate` mutation instead.",
                        code=OrderErrorCode.INVALID,
                    )
                }
            )
        return instance

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info, instance, cleaned_input):
        cls._save_addresses(info, instance, cleaned_input)
        if instance.user_email:
            user = User.objects.filter(email=instance.user_email).first()
            instance.user = user
        instance.save()
        update_order_prices(
            instance,
            info.context.plugins,
            info.context.site.settings.include_taxes_in_prices,
        )
        info.context.plugins.order_updated(instance)


class OrderUpdateShippingInput(graphene.InputObjectType):
    shipping_method = graphene.ID(
        description="ID of the selected shipping method.", name="shippingMethod"
    )


class EditableOrderValidationMixin:
    class Meta:
        abstract = True

    @classmethod
    def validate_order(cls, order):
        if order.status not in ORDER_EDITABLE_STATUS:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Only draft and unconfirmed orders can be edited.",
                        code=OrderErrorCode.NOT_EDITABLE,
                    )
                }
            )


class OrderUpdateShipping(EditableOrderValidationMixin, BaseMutation):
    order = graphene.Field(Order, description="Order with updated shipping method.")

    class Arguments:
        id = graphene.ID(
            required=True,
            name="order",
            description="ID of the order to update a shipping method.",
        )
        input = OrderUpdateShippingInput(
            description="Fields required to change shipping method of the order."
        )

    class Meta:
        description = "Updates a shipping method of the order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(
            info,
            data.get("id"),
            only_type=Order,
            qs=models.Order.objects.prefetch_related("lines"),
        )
        cls.validate_order(order)
        data = data.get("input")

        if not data["shipping_method"]:
            if not order.is_draft() and order.is_shipping_required():
                raise ValidationError(
                    {
                        "shipping_method": ValidationError(
                            "Shipping method is required for this order.",
                            code=OrderErrorCode.SHIPPING_METHOD_REQUIRED,
                        )
                    }
                )

            order.shipping_method = None
            order.shipping_price = zero_taxed_money(order.currency)
            order.shipping_method_name = None
            order.save(
                update_fields=[
                    "currency",
                    "shipping_method",
                    "shipping_price_net_amount",
                    "shipping_price_gross_amount",
                    "shipping_method_name",
                ]
            )
            return OrderUpdateShipping(order=order)

        method = cls.get_node_or_error(
            info,
            data["shipping_method"],
            field="shipping_method",
            only_type=ShippingMethod,
            qs=shipping_models.ShippingMethod.objects.prefetch_related(
                "postal_code_rules"
            ),
        )

        clean_order_update_shipping(order, method)

        order.shipping_method = method
        shipping_price = info.context.plugins.calculate_order_shipping(order)
        order.shipping_price = shipping_price
        order.shipping_tax_rate = info.context.plugins.get_order_shipping_tax_rate(
            order, shipping_price
        )
        order.shipping_method_name = method.name
        order.save(
            update_fields=[
                "currency",
                "shipping_method",
                "shipping_method_name",
                "shipping_price_net_amount",
                "shipping_price_gross_amount",
                "shipping_tax_rate",
            ]
        )
        update_order_prices(
            order,
            info.context.plugins,
            info.context.site.settings.include_taxes_in_prices,
        )
        # Post-process the results
        order_shipping_updated(order, info.context.plugins)
        return OrderUpdateShipping(order=order)


class OrderAddNoteInput(graphene.InputObjectType):
    message = graphene.String(
        description="Note message.", name="message", required=True
    )


class OrderAddNote(BaseMutation):
    order = graphene.Field(Order, description="Order with the note added.")
    event = graphene.Field(OrderEvent, description="Order note created.")

    class Arguments:
        id = graphene.ID(
            required=True,
            description="ID of the order to add a note for.",
            name="order",
        )
        input = OrderAddNoteInput(
            required=True, description="Fields required to create a note for the order."
        )

    class Meta:
        description = "Adds note to the order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_input(cls, _info, _instance, data):
        try:
            cleaned_input = validate_required_string_field(data["input"], "message")
        except ValidationError:
            raise ValidationError(
                {
                    "message": ValidationError(
                        "Message can't be empty.",
                        code=OrderErrorCode.REQUIRED,
                    )
                }
            )
        return cleaned_input

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        cleaned_input = cls.clean_input(info, order, data)
        event = events.order_note_added_event(
            order=order,
            user=info.context.user,
            app=info.context.app,
            message=cleaned_input["message"],
        )
        return OrderAddNote(order=order, event=event)


class OrderCancel(BaseMutation):
    order = graphene.Field(Order, description="Canceled order.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to cancel.")

    class Meta:
        description = "Cancel an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        clean_order_cancel(order)
        cancel_order(
            order=order,
            user=info.context.user,
            app=info.context.app,
            manager=info.context.plugins,
        )
        return OrderCancel(order=order)


class OrderMarkAsPaid(BaseMutation):
    order = graphene.Field(Order, description="Order marked as paid.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to mark paid.")
        transaction_reference = graphene.String(
            required=False, description="The external transaction reference."
        )

    class Meta:
        description = "Mark order as manually paid."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_billing_address(cls, instance):
        if not instance.billing_address:
            raise ValidationError(
                "Order billing address is required to mark order as paid.",
                code=OrderErrorCode.BILLING_ADDRESS_NOT_SET,
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        transaction_reference = data.get("transaction_reference")
        cls.clean_billing_address(order)
        user = info.context.user
        app = info.context.app
        try_payment_action(order, user, app, None, clean_mark_order_as_paid, order)

        mark_order_as_paid(
            order, user, app, info.context.plugins, transaction_reference
        )
        return OrderMarkAsPaid(order=order)


class OrderCapture(BaseMutation):
    order = graphene.Field(Order, description="Captured order.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to capture.")
        amount = PositiveDecimal(
            required=True, description="Amount of money to capture."
        )

    class Meta:
        description = "Capture an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(cls, _root, info, amount, **data):
        if amount <= 0:
            raise ValidationError(
                {
                    "amount": ValidationError(
                        "Amount should be a positive number.",
                        code=OrderErrorCode.ZERO_QUANTITY,
                    )
                }
            )

        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        payment = order.get_last_payment()
        clean_order_capture(payment)

        transaction = try_payment_action(
            order,
            info.context.user,
            info.context.app,
            payment,
            gateway.capture,
            payment,
            info.context.plugins,
            amount=amount,
            channel_slug=order.channel.slug,
        )
        # Confirm that we changed the status to capture. Some payment can receive
        # asynchronous webhook with update status
        if transaction.kind == TransactionKind.CAPTURE:
            order_captured(
                order,
                info.context.user,
                info.context.app,
                amount,
                payment,
                info.context.plugins,
            )
        return OrderCapture(order=order)


class OrderVoid(BaseMutation):
    order = graphene.Field(Order, description="A voided order.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to void.")

    class Meta:
        description = "Void an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        payment = order.get_last_payment()
        clean_void_payment(payment)

        transaction = try_payment_action(
            order,
            info.context.user,
            info.context.app,
            payment,
            gateway.void,
            payment,
            info.context.plugins,
            channel_slug=order.channel.slug,
        )
        # Confirm that we changed the status to void. Some payment can receive
        # asynchronous webhook with update status
        if transaction.kind == TransactionKind.VOID:
            order_voided(
                order,
                info.context.user,
                info.context.app,
                payment,
                info.context.plugins,
            )
        return OrderVoid(order=order)


class OrderRefund(BaseMutation):
    order = graphene.Field(Order, description="A refunded order.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to refund.")
        amount = PositiveDecimal(
            required=True, description="Amount of money to refund."
        )

    class Meta:
        description = "Refund an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(cls, _root, info, amount, **data):
        if amount <= 0:
            raise ValidationError(
                {
                    "amount": ValidationError(
                        "Amount should be a positive number.",
                        code=OrderErrorCode.ZERO_QUANTITY,
                    )
                }
            )

        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        payment = order.get_last_payment()
        clean_refund_payment(payment)

        transaction = try_payment_action(
            order,
            info.context.user,
            info.context.app,
            payment,
            gateway.refund,
            payment,
            info.context.plugins,
            amount=amount,
            channel_slug=order.channel.slug,
        )
        order.fulfillments.create(
            status=FulfillmentStatus.REFUNDED, total_refund_amount=amount
        )

        # Confirm that we changed the status to refund. Some payment can receive
        # asynchronous webhook with update status
        if transaction.kind == TransactionKind.REFUND:
            order_refunded(
                order,
                info.context.user,
                info.context.app,
                amount,
                payment,
                info.context.plugins,
            )
        return OrderRefund(order=order)


class OrderConfirm(ModelMutation):
    order = graphene.Field(Order, description="Order which has been confirmed.")

    class Arguments:
        id = graphene.ID(description="ID of an order to confirm.", required=True)

    class Meta:
        description = "Confirms an unconfirmed order by changing status to unfulfilled."
        model = models.Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def get_instance(cls, info, **data):
        instance = super().get_instance(info, **data)
        if not instance.is_unconfirmed():
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to an order with status "
                        "different than unconfirmed.",
                        code=OrderErrorCode.INVALID,
                    )
                }
            )
        if not instance.lines.exists():
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to an order without products.",
                        code=OrderErrorCode.INVALID,
                    )
                }
            )
        return instance

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, root, info, **data):
        order = cls.get_instance(info, **data)
        order.status = OrderStatus.UNFULFILLED
        order.save(update_fields=["status"])
        payment = order.get_last_payment()
        manager = info.context.plugins
        if payment and payment.is_authorized and payment.can_capture():
            gateway.capture(
                payment, info.context.plugins, channel_slug=order.channel.slug
            )
            order_captured(
                order,
                info.context.user,
                info.context.app,
                payment.total,
                payment,
                manager,
            )
        order_confirmed(
            order,
            info.context.user,
            info.context.app,
            manager,
            send_confirmation_email=True,
        )
        return OrderConfirm(order=order)


class OrderLinesCreate(EditableOrderValidationMixin, BaseMutation):
    order = graphene.Field(Order, description="Related order.")
    order_lines = graphene.List(
        graphene.NonNull(OrderLine), description="List of added order lines."
    )

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the order to add the lines to."
        )
        input = graphene.List(
            OrderLineCreateInput,
            required=True,
            description="Fields required to add order lines.",
        )

    class Meta:
        description = "Create order lines for an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"
        errors_mapping = {"lines": "input", "channel": "input"}

    @classmethod
    def validate_lines(cls, info, data):
        lines_to_add = []
        invalid_ids = []
        for input_line in data.get("input"):
            variant_id = input_line["variant_id"]
            variant = cls.get_node_or_error(
                info, variant_id, "variant_id", only_type=ProductVariant
            )
            quantity = input_line["quantity"]
            if quantity > 0:
                lines_to_add.append((quantity, variant))
            else:
                invalid_ids.append(variant_id)
        if invalid_ids:
            raise ValidationError(
                {
                    "quantity": ValidationError(
                        "Variants quantity must be greater than 0.",
                        code=OrderErrorCode.ZERO_QUANTITY,
                        params={"variants": invalid_ids},
                    ),
                }
            )
        return lines_to_add

    @classmethod
    def validate_variants(cls, order, variants):
        try:
            channel = order.channel
            validate_product_is_published_in_channel(variants, channel)
            validate_variant_channel_listings(variants, channel)
        except ValidationError as error:
            cls.remap_error_fields(error, cls._meta.errors_mapping)
            raise ValidationError(error)

    @staticmethod
    def add_lines_to_order(order, lines_to_add, user, app, manager):
        try:
            return [
                add_variant_to_order(
                    order,
                    variant,
                    quantity,
                    user,
                    app,
                    manager,
                    allocate_stock=order.is_unconfirmed(),
                )
                for quantity, variant in lines_to_add
            ]
        except TaxError as tax_error:
            raise ValidationError(
                "Unable to calculate taxes - %s" % str(tax_error),
                code=OrderErrorCode.TAX_ERROR.value,
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        cls.validate_order(order)
        lines_to_add = cls.validate_lines(info, data)
        variants = [line[1] for line in lines_to_add]
        cls.validate_variants(order, variants)

        lines = cls.add_lines_to_order(
            order,
            lines_to_add,
            info.context.user,
            info.context.app,
            info.context.plugins,
        )

        # Create the products added event
        events.order_added_products_event(
            order=order,
            user=info.context.user,
            app=info.context.app,
            order_lines=lines_to_add,
        )

        recalculate_order(order)
        return OrderLinesCreate(order=order, order_lines=lines)


class OrderLineDelete(EditableOrderValidationMixin, BaseMutation):
    order = graphene.Field(Order, description="A related order.")
    order_line = graphene.Field(
        OrderLine, description="An order line that was deleted."
    )

    class Arguments:
        id = graphene.ID(description="ID of the order line to delete.", required=True)

    class Meta:
        description = "Deletes an order line from an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(cls, _root, info, id):
        line = cls.get_node_or_error(
            info,
            id,
            only_type=OrderLine,
        )
        order = line.order
        cls.validate_order(line.order)

        db_id = line.id
        warehouse_pk = (
            line.allocations.first().stock.warehouse.pk
            if order.is_unconfirmed()
            else None
        )
        line_info = OrderLineData(
            line=line,
            quantity=line.quantity,
            variant=line.variant,
            warehouse_pk=warehouse_pk,
        )
        delete_order_line(line_info)
        line.id = db_id

        # Create the removal event
        events.order_removed_products_event(
            order=order,
            user=info.context.user,
            app=info.context.app,
            order_lines=[(line.quantity, line)],
        )

        recalculate_order(order)
        return OrderLineDelete(order=order, order_line=line)


class OrderLineUpdate(EditableOrderValidationMixin, ModelMutation):
    order = graphene.Field(Order, description="Related order.")

    class Arguments:
        id = graphene.ID(description="ID of the order line to update.", required=True)
        input = OrderLineInput(
            required=True, description="Fields required to update an order line."
        )

    class Meta:
        description = "Updates an order line of an order."
        model = models.OrderLine
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        instance.old_quantity = instance.quantity
        cleaned_input = super().clean_input(info, instance, data)
        cls.validate_order(instance.order)

        quantity = data["quantity"]
        if quantity <= 0:
            raise ValidationError(
                {
                    "quantity": ValidationError(
                        "Ensure this value is greater than 0.",
                        code=OrderErrorCode.ZERO_QUANTITY,
                    )
                }
            )
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        warehouse_pk = (
            instance.allocations.first().stock.warehouse.pk
            if instance.order.is_unconfirmed()
            else None
        )
        line_info = OrderLineData(
            line=instance,
            quantity=instance.quantity,
            variant=instance.variant,
            warehouse_pk=warehouse_pk,
        )
        try:
            change_order_line_quantity(
                info.context.user,
                info.context.app,
                line_info,
                instance.old_quantity,
                instance.quantity,
                instance.order.channel.slug,
            )
        except InsufficientStock:
            raise ValidationError(
                "Cannot set new quantity because of insufficient stock.",
                code=OrderErrorCode.INSUFFICIENT_STOCK,
            )
        recalculate_order(instance.order)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.order = instance.order
        return response
