import graphene
from django.utils.translation import npgettext_lazy, pgettext_lazy
from graphql_jwt.decorators import permission_required
from payments import PaymentError, PaymentStatus

from ....order import CustomPaymentChoices, models
from ....order.utils import cancel_order
from ...core.mutations import BaseMutation, ModelMutation
from ...core.types import Decimal, Error
from ...order.mutations.draft_orders import DraftOrderUpdate
from ...order.types import Order
from ...utils import get_node
from .draft_orders import AddressInput


def try_payment_action(action, money, errors):
    try:
        action(money)
    except (PaymentError, ValueError) as e:
        errors.append(Error(field='payment', message=str(e)))


def clean_release_payment(payment):
    """Check for payment errors."""
    errors = []
    if payment.status != PaymentStatus.PREAUTH:
        errors.append(
            Error(field='payment',
                  message='Only pre-authorized payments can be released'))
    try:
        payment.release()
    except (PaymentError, ValueError) as e:
        errors.append(Error(field='payment', message=str(e)))
    return errors


def clean_refund_payment(payment, amount):
    errors = []
    if payment.variant == CustomPaymentChoices.MANUAL:
        errors.append(
            Error(field='payment',
                  message='Manual payments can not be refunded.'))
    try_payment_action(payment.refund, amount, errors)
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


class OrderAddNoteInput(graphene.InputObjectType):
    order = graphene.ID(description='ID of the order.')
    user = graphene.ID(description='ID of the user who added note.')
    content = graphene.String(description='Note content.')
    is_public = graphene.Boolean(
        description='Determine if note is visible by customer or not.')


class OrderAddNote(ModelMutation):
    class Arguments:
        input = OrderAddNoteInput(
            required=True,
            description='Fields required to add note to order.')

    class Meta:
        description = 'Adds note to order.'
        model = models.OrderNote

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('order.edit_order')

    @classmethod
    def save(cls, info, instance, cleaned_input):
        super().save(info, instance, cleaned_input)
        msg = pgettext_lazy(
            'Dashboard message related to an order', 'Added note')
        instance.order.history.create(content=msg, user=info.context.user)


class OrderCancel(BaseMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of the order to cancel.')
        restock = graphene.Boolean(
            required=True,
            description='Determine if lines will be restocked or not.')

    class Meta:
        description = 'Cancel an order.'

    order = graphene.Field(
        Order, description='Canceled order.')

    @classmethod
    @permission_required('order.edit_order')
    def mutate(cls, root, info, id, restock):
        order = get_node(info, id, only_type=Order)
        cancel_order(order=order, restock=restock)
        if restock:
            restock_msg = npgettext_lazy(
                'Dashboard message related to an order',
                'Restocked %(quantity)d item',
                'Restocked %(quantity)d items',
                'quantity') % {'quantity': order.get_total_quantity()}
            order.history.create(content=restock_msg, user=info.context.user)
        else:
            msg = pgettext_lazy(
                'Dashboard message related to an order', 'Order canceled')
            order.history.create(content=msg, user=info.context.user)
        return OrderCancel(order=order)


class OrderMarkAsPaid(BaseMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of the order to mark paid.')

    class Meta:
        description = 'Mark order as manually paid.'

    order = graphene.Field(
        Order, description='Order marked as paid.')

    @classmethod
    @permission_required('order.edit_order')
    def mutate(cls, root, info, id):
        order = get_node(info, id, only_type=Order)
        if order.payments.exists():
            field = 'payment'
            msg = 'Orders with payments can not be manually marked as paid.'
            return cls(errors=[Error(field=field, message=msg)])
        defaults = {
            'total': order.total.gross.amount,
            'tax': order.total.tax.amount,
            'currency': order.total.currency,
            'delivery': order.shipping_price.net.amount,
            'description': pgettext_lazy(
                'Payment description', 'Order %(order)s') % {'order': order},
            'captured_amount': order.total.gross.amount}
        models.Payment.objects.get_or_create(
            variant=CustomPaymentChoices.MANUAL,
            status=PaymentStatus.CONFIRMED, order=order,
            defaults=defaults)
        msg = pgettext_lazy(
            'Dashboard message related to an order',
            'Order manually marked as paid.')
        order.history.create(content=msg, user=info.context.user)
        return OrderMarkAsPaid(order=order)


class OrderCapture(BaseMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of the order to capture.')
        amount = Decimal(
            required=True, description='Amount of money to capture.')

    class Meta:
        description = 'Capture an order.'

    order = graphene.Field(
        Order, description='Captured order.')

    @classmethod
    @permission_required('order.edit_order')
    def mutate(cls, root, info, id, amount):
        order = get_node(info, id, only_type=Order)
        payment = order.get_last_payment()
        errors = []
        try_payment_action(payment.capture, amount, errors)
        if errors:
            return cls(errors=errors)

        msg = pgettext_lazy(
            'Dashboard message related to an order',
            'Captured %(amount)s' % {'amount': amount})
        order.history.create(content=msg, user=info.context.user)
        return OrderCapture(order=order)


class OrderRelease(BaseMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of the order to release.')

    class Meta:
        description = 'Release an order.'

    order = graphene.Field(
        Order, description='A released order.')

    @classmethod
    @permission_required('order.edit_order')
    def mutate(cls, root, info, id):
        order = get_node(info, id, only_type=Order)
        payment = order.get_last_payment()
        errors = clean_release_payment(payment)
        if errors:
            return cls(errors=errors)

        msg = pgettext_lazy(
            'Dashboard message related to an order',
            'Released payment')
        order.history.create(content=msg, user=info.context.user)
        return OrderRelease(order=order)


class OrderRefund(BaseMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of the order to refund.')
        amount = Decimal(
            required=True, description='Amount of money to refund.')

    class Meta:
        description = 'Refund an order.'

    order = graphene.Field(
        Order, description='A refunded order.')

    @classmethod
    @permission_required('order.edit_order')
    def mutate(cls, root, info, id, amount):
        order = get_node(info, id, only_type=Order)
        payment = order.get_last_payment()
        errors = clean_refund_payment(payment, amount)
        if errors:
            return cls(errors=errors)

        msg = pgettext_lazy(
            'Dashboard message related to an order',
            'Refunded %(amount)s' % {'amount': amount})
        order.history.create(content=msg, user=info.context.user)
        return OrderRefund(order=order)
