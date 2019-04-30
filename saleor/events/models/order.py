from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.timezone import now

from ...account.models import Address
from ...core.utils.json_serializer import CustomJsonEncoder
from ...order.models import Fulfillment, Order, OrderLine
from ...payment.models import Payment
from ...product.models import ProductVariant
from .. import OrderEvents, OrderEventsEmails

UserType = AbstractBaseUser


def _lines_per_quantity_to_str_line_list(quantities_per_order_line):
    return [{
        'quantity': quantity,
        'item': str(line)
    } for quantity, line in quantities_per_order_line]


def _get_payment_data(
        amount: Optional[Decimal], payment: Payment) -> Dict:
    return {
        'parameters': {
            'amount': amount,
            'payment_id': payment.token,
            'payment_gateway': payment.gateway}}


class OrderEvent(models.Model):
    """Model used to store events that happened during the order lifecycle.

    Args:
        parameters: Values needed to display the event on the storefront
        type: Type of an order
    """

    date = models.DateTimeField(default=now, editable=False)
    type = models.CharField(
        max_length=255,
        choices=((event.name, event.value) for event in OrderEvents))
    order = models.ForeignKey(
        Order, related_name='events', on_delete=models.CASCADE)
    parameters = JSONField(
        blank=True, default=dict, encoder=CustomJsonEncoder)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        on_delete=models.SET_NULL, related_name='+')

    class Meta:
        ordering = ('date', )

    def __repr__(self):
        return 'OrderEvent(type=%r, user=%r)' % (self.type, self.user)

    @classmethod
    def email_sent_event(
            cls, *,
            order: Order, email_type: OrderEventsEmails,
            user: Optional[UserType]) -> models.Model:

        if user is not None and user.is_anonymous:
            user = None

        return cls(
            order=order, type=OrderEvents.EMAIL_SENT.value,
            user=user,
            parameters={
                'email': order.get_user_current_email(),
                'email_type': email_type.value})

    @classmethod
    def email_resent_event(
            cls, *,
            order: Order, email_type: OrderEventsEmails,
            user: UserType) -> models.Model:
        raise NotImplementedError

    @classmethod
    def draft_order_created_event(
            cls, *, order: Order, user: UserType) -> models.Model:
        return cls(
            order=order, type=OrderEvents.DRAFT_CREATED.value, user=user)

    @classmethod
    def draft_order_added_products_event(
            cls, *,
            order: Order, user: UserType,
            order_lines: List[Tuple[int, ProductVariant]]) -> models.Model:

        return cls(
            order=order, type=OrderEvents.DRAFT_ADDED_PRODUCTS.value,
            user=user,
            parameters={
                'lines': _lines_per_quantity_to_str_line_list(order_lines)})

    @classmethod
    def draft_order_removed_products_event(
            cls, *,
            order: Order, user: UserType,
            order_lines: List[Tuple[int, ProductVariant]]
    ) -> models.Model:

        return cls(
            order=order, type=OrderEvents.DRAFT_REMOVED_PRODUCTS.value,
            user=user,
            parameters={
                'lines': _lines_per_quantity_to_str_line_list(order_lines)})

    @classmethod
    def order_created_event(
            cls, order: Order, user: UserType,
            from_draft=False) -> models.Model:
        event_type = (
            OrderEvents.PLACED_FROM_DRAFT if from_draft else OrderEvents.PLACED
        )

        if user.is_anonymous:
            user = None

        return cls(
            order=order, type=event_type.value, user=user)

    @classmethod
    def draft_order_oversold_items_event(
            cls, *,
            order: Order, user: UserType,
            oversold_items: List[str]) -> models.Model:
        return cls(
            order=order, type=OrderEvents.OVERSOLD_ITEMS.value,
            user=user,
            parameters={
                'oversold_items': oversold_items})

    @classmethod
    def order_canceled_event(
            cls, *,
            order: Order, user: UserType) -> models.Model:
        return cls(
            order=order, type=OrderEvents.CANCELED.value,
            user=user)

    @classmethod
    def order_manually_marked_as_paid_event(
            cls, *,
            order: Order, user: UserType) -> models.Model:
        return cls(
            order=order, type=OrderEvents.ORDER_MARKED_AS_PAID.value,
            user=user)

    @classmethod
    def order_fully_paid_event(cls, *, order: Order) -> models.Model:
        return cls(order=order, type=OrderEvents.ORDER_FULLY_PAID.value)

    @classmethod
    def payment_captured_event(
            cls, *,
            order: Order, user: UserType,
            amount: Decimal, payment: Payment) -> models.Model:
        return cls(
            order=order, type=OrderEvents.PAYMENT_CAPTURED.value,
            user=user, **_get_payment_data(amount, payment))

    @classmethod
    def payment_refunded_event(
            cls, *,
            order: Order, user: UserType,
            amount: Decimal, payment: Payment) -> models.Model:
        return cls(
            order=order, type=OrderEvents.PAYMENT_REFUNDED.value,
            user=user, **_get_payment_data(amount, payment))

    @classmethod
    def payment_voided_event(
            cls, *,
            order: Order, user: UserType, payment: Payment) -> models.Model:
        return cls(
            order=order, type=OrderEvents.PAYMENT_VOIDED.value,
            user=user, **_get_payment_data(None, payment))

    @classmethod
    def payment_failed_event(
            cls, *,
            order: Order, user: UserType, message: str,
            payment: Payment) -> models.Model:

        parameters = {'message': message}

        if payment:
            parameters.update({
                'gateway': payment.gateway,
                'payment_id': payment.token})

        return cls(
            order=order, type=OrderEvents.PAYMENT_FAILED.value,
            user=user, parameters=parameters)

    @classmethod
    def fulfillment_canceled_event(
            cls, *,
            order: Order, user: UserType,
            fulfillment: Fulfillment) -> models.Model:
        return cls(
            order=order, type=OrderEvents.FULFILLMENT_CANCELED.value,
            user=user,
            parameters={'composed_id': fulfillment.composed_id})

    @classmethod
    def fulfillment_restocked_items_event(
            cls, *,
            order: Order, user: UserType,
            fulfillment: Union[Order, Fulfillment]) -> models.Model:
        return cls(
            order=order, type=OrderEvents.FULFILLMENT_RESTOCKED_ITEMS.value,
            user=user,
            parameters={
                'quantity': fulfillment.get_total_quantity()})

    @classmethod
    def fulfillment_fulfilled_items_event(
            cls, *,
            order: Order, user: UserType,
            quantities: List[int],
            order_lines: List[OrderLine]) -> models.Model:
        return cls(
            order=order, type=OrderEvents.FULFILLMENT_FULFILLED_ITEMS.value,
            user=user,
            parameters={
                'lines': _lines_per_quantity_to_str_line_list(
                    zip(quantities, order_lines))})

    @classmethod
    def fulfillment_tracking_updated_event(
            cls, *,
            order: Order, user: UserType,
            tracking_number: str,
            fulfillment: Fulfillment) -> models.Model:
        return cls(
            order=order, type=OrderEvents.TRACKING_UPDATED.value,
            user=user,
            parameters={
                'tracking_number': tracking_number,
                'fulfillment': fulfillment.composed_id})

    @classmethod
    def order_note_added_event(
            cls, *,
            order: Order, user: UserType, message: str) -> models.Model:
        return cls(
            order=order, type=OrderEvents.NOTE_ADDED.value,
            user=user,
            parameters={
                'message': message})

    @classmethod
    def order_updated_address_event(
            cls, *,
            order: Order, user: UserType, address: Address) -> models.Model:
        return cls(
            order=order, type=OrderEvents.UPDATED_ADDRESS.value,
            user=user,
            parameters={
                'new_address': str(address)})
