import graphene
from graphql_jwt.decorators import permission_required

from ....account.models import User
from ....core.utils.taxes import ZERO_TAXED_MONEY
from ....order import CustomPaymentChoices, OrderEvents, models
from ....order.utils import cancel_order
from ....payment import ChargeStatus, PaymentError
from ....payment.models import PaymentMethod
from ....shipping.models import ShippingMethod as ShippingMethodModel
from ...account.types import AddressInput
from ...core.mutations import BaseMutation
from ...core.types.common import Decimal, Error
from ...order.mutations.draft_orders import DraftOrderUpdate
from ...order.types import Order, OrderEvent
from ...shipping.types import ShippingMethod


def clean_order_update_shipping(order, method, errors):
    if not method:
        return errors
    if not order.shipping_address:
        errors.append(
            Error(
                field='order',
                message=(
                    'Cannot choose a shipping method for an '
                    'order without the shipping address.')))
        return errors
    valid_methods = (
        ShippingMethodModel.objects.applicable_shipping_methods(
            price=order.get_subtotal().gross.amount,
            weight=order.get_total_weight(),
            country_code=order.shipping_address.country.code))
    valid_methods = valid_methods.values_list('id', flat=True)
    if method.pk not in valid_methods:
        errors.append(
            Error(
                field='shippingMethod',
                message='Shipping method cannot be used with this order.'))
    return errors


def try_payment_action(action, money, errors):
    try:
        action(money)
    except (PaymentError, ValueError) as e:
        errors.append(Error(field='payment', message=str(e)))


def clean_order_cancel(order, errors):
    if order and not order.can_cancel():
        errors.append(
            Error(
                field='order',
                message='This order can\'t be canceled.'))
    return errors


def clean_order_mark_as_paid(order, errors):
    if order and order.payment_methods.exists():
        errors.append(
            Error(
                field='payment',
                message='Orders with payments can not be manually '
                        'marked as paid.'))
    return errors


def clean_order_capture(payment, amount, errors):
    if not payment:
        errors.append(
            Error(
                field='payment',
                message='There\'s no payment associated with the order.'))
        return errors
    if not payment.is_active:
        errors.append(
            Error(
                field='payment',
                message='Only pre-authorized payments can be captured'))
    return errors


def clean_release_payment(payment, errors):
    """Check for payment errors."""
    if not payment.is_active:
        errors.append(
            Error(field='payment',
                  message='Only pre-authorized payments can be released'))
    try:
        payment.void()
    except (PaymentError, ValueError) as e:
        errors.append(Error(field='payment', message=str(e)))
    return errors


def clean_refund_payment(payment, amount, errors):
    if payment.variant == CustomPaymentChoices.MANUAL:
        errors.append(
            Error(field='payment',
                  message='Manual payments can not be refunded.'))
    return errors


class OrderUpdateInput(graphene.InputObjectType):
    billing_address = AddressInput(
        description='Billing address of the customer.')
    user_email = graphene.String(description='Email address of the customer.')
    shipping_address = AddressInput(
        description='Shipping address of the customer.')


class OrderUpdate(DraftOrderUpdate):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an order to update.')
        input = OrderUpdateInput(
            required=True,
            description='Fields required to update an order.')

    class Meta:
        description = 'Updates an order.'
        model = models.Order

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        if not instance.user and not cleaned_input.get('user_email'):
            cls.add_error(
                errors, field='user_email',
                message='User_email field is null while order was created by '
                        'anonymous user')
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        super().save(info, instance, cleaned_input)
        if instance.user_email:
            user = User.objects.filter(email=instance.user_email).first()
            instance.user = user
        instance.save()


class OrderUpdateShippingInput(graphene.InputObjectType):
    shipping_method = graphene.ID(
        description='ID of the selected shipping method.',
        name='shippingMethod')


class OrderUpdateShipping(BaseMutation):
    order = graphene.Field(
        Order, description='Order with updated shipping method.')

    class Arguments:
        id = graphene.ID(
            required=True, name='order',
            description='ID of the order to update a shipping method.')
        input = OrderUpdateShippingInput(
            description='Fields required to change '
                        'shipping method of the order.')

    class Meta:
        description = 'Updates a shipping method of the order.'

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, id, input):
        errors = []
        order = cls.get_node_or_error(info, id, errors, 'id', Order)

        if not input['shipping_method']:
            if order.is_shipping_required():
                cls.add_error(
                    errors, 'shippingMethod',
                    'Shipping method is required for this order.')
                return OrderUpdateShipping(errors=errors)
            order.shipping_method = None
            order.shipping_price = ZERO_TAXED_MONEY
            order.shipping_method_name = None
            order.save(
                update_fields=[
                    'shipping_method', 'shipping_price_net',
                    'shipping_price_gross', 'shipping_method_name'])
            return OrderUpdateShipping(order=order)

        method = cls.get_node_or_error(
            info, input['shipping_method'], errors,
            'shipping_method', ShippingMethod)
        clean_order_update_shipping(order, method, errors)
        if errors:
            return OrderUpdateShipping(errors=errors)

        order.shipping_method = method
        order.shipping_price = method.get_total(info.context.taxes)
        order.shipping_method_name = method.name
        order.save(
            update_fields=[
                'shipping_method', 'shipping_method_name',
                'shipping_price_net', 'shipping_price_gross'])
        return OrderUpdateShipping(order=order)


class OrderAddNoteInput(graphene.InputObjectType):
    message = graphene.String(description='Note message.', name='message')


class OrderAddNote(BaseMutation):
    order = graphene.Field(Order, description='Order with the note added.')
    event = graphene.Field(OrderEvent, description='Order note created.')

    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of the order to add a note for.', name='order')
        input = OrderAddNoteInput(
            required=True,
            description='Fields required to create a note for the order.')

    class Meta:
        description = 'Adds note to the order.'

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, id, input):
        errors = []
        order = cls.get_node_or_error(info, id, errors, 'id', Order)
        if errors:
            return OrderAddNote(errors=errors)

        event = order.events.create(
            type=OrderEvents.NOTE_ADDED.value,
            user=info.context.user,
            parameters={
                'message': input['message']})
        return OrderAddNote(order=order, event=event)


class OrderCancel(BaseMutation):
    order = graphene.Field(Order, description='Canceled order.')

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of the order to cancel.')
        restock = graphene.Boolean(
            required=True,
            description='Determine if lines will be restocked or not.')

    class Meta:
        description = 'Cancel an order.'

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, id, restock):
        errors = []
        order = cls.get_node_or_error(info, id, errors, 'id', Order)
        clean_order_cancel(order, errors)
        if errors:
            return OrderCancel(errors=errors)

        cancel_order(order=order, restock=restock)
        if restock:
            order.events.create(
                type=OrderEvents.FULFILLMENT_RESTOCKED_ITEMS.value,
                user=info.context.user,
                parameters={'quantity': order.get_total_quantity()})
        else:
            order.events.create(
                type=OrderEvents.CANCELED.value, user=info.context.user)
        return OrderCancel(order=order)


class OrderMarkAsPaid(BaseMutation):
    order = graphene.Field(Order, description='Order marked as paid.')

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of the order to mark paid.')

    class Meta:
        description = 'Mark order as manually paid.'

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, id):
        errors = []
        order = cls.get_node_or_error(info, id, errors, 'id', Order)
        clean_order_mark_as_paid(order, errors)
        if errors:
            return OrderMarkAsPaid(errors=errors)
        # FIXME add more fields to the payment method
        defaults = {
            'total': order.total, 'captured_amount': order.total.gross}
        PaymentMethod.objects.get_or_create(
            variant=CustomPaymentChoices.MANUAL,
            charge_status=ChargeStatus.CHARGED, order=order,
            defaults=defaults)

        order.events.create(
            type=OrderEvents.ORDER_MARKED_AS_PAID.value,
            user=info.context.user)
        return OrderMarkAsPaid(order=order)


class OrderCapture(BaseMutation):
    order = graphene.Field(Order, description='Captured order.')

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of the order to capture.')
        amount = Decimal(
            required=True, description='Amount of money to capture.')

    class Meta:
        description = 'Capture an order.'

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, id, amount):
        # FIXME we should validate if amount is positive number
        errors = []
        order = cls.get_node_or_error(info, id, errors, 'id', Order)
        payment = order.get_last_payment()
        clean_order_capture(payment, amount, errors)
        try_payment_action(payment.capture, amount, errors)
        if errors:
            return OrderCapture(errors=errors)

        order.events.create(
            parameters={'amount': amount},
            type=OrderEvents.PAYMENT_CAPTURED.value,
            user=info.context.user)
        return OrderCapture(order=order)


class OrderRelease(BaseMutation):
    order = graphene.Field(Order, description='A released order.')

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of the order to release.')

    class Meta:
        description = 'Release an order.'

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, id):
        errors = []
        order = cls.get_node_or_error(info, id, errors, 'id', Order)
        if order:
            payment = order.get_last_payment()
            clean_release_payment(payment, errors)

        if errors:
            return OrderRelease(errors=errors)
        order.events.create(
            type=OrderEvents.PAYMENT_RELEASED.value,
            user=info.context.user)
        return OrderRelease(order=order)


class OrderRefund(BaseMutation):
    order = graphene.Field(Order, description='A refunded order.')

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of the order to refund.')
        amount = Decimal(
            required=True, description='Amount of money to refund.')

    class Meta:
        description = 'Refund an order.'

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, id, amount):
        # FIXME we should validate if amount is positive number
        errors = []
        order = cls.get_node_or_error(info, id, errors, 'id', Order)
        if order:
            payment = order.get_last_payment()
            clean_refund_payment(payment, amount, errors)
            try_payment_action(payment.refund, amount, errors)
        if errors:
            return OrderRefund(errors=errors)

        order.events.create(
            type=OrderEvents.PAYMENT_REFUNDED.value,
            user=info.context.user,
            parameters={'amount': amount})
        return OrderRefund(order=order)
