from typing import Dict, List, Union

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.timezone import now
from prices import Money

from ...account.models import Address
from ...core.utils.json_serializer import CustomJsonEncoder
from ...order.models import Fulfillment, Order, OrderLine
from ...payment.models import Payment
from ...product.models import ProductVariant
from ..lang.order_events import display_order_event
from ..types import OrderEvents, OrderEventsEmails

User = AbstractBaseUser


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
        db_table = 'order_orderevent'

    def __repr__(self):
        return 'OrderEvent(type=%r, user=%r)' % (self.type, self.user)

    def get_event_display(self):
        return display_order_event(self)

    @classmethod
    def email_sent_event(
            cls, *,
            order: Order, email_type: OrderEventsEmails,
            source: Union[User, None]) -> models.Model:
        return cls(
            order=order, type=OrderEvents.EMAIL_SENT.value,
            user=source,
            parameters={
                'email': order.get_user_current_email(),
                'email_type': email_type.value})

    @classmethod
    def email_resent_event(
            cls, *,
            order: Order, email_type: OrderEventsEmails,
            source: User) -> models.Model:
        raise NotImplementedError

    @classmethod
    def draft_created_event(
            cls, *, order: Order, source: User) -> models.Model:
        return cls(
            order=order, type=OrderEvents.DRAFT_CREATED.value, user=source)

    @classmethod
    def draft_selected_shipping_method_event(
            cls, order: Order) -> models.Model:
        raise NotImplementedError

    @classmethod
    def draft_added_products(
            cls, *,
            order: Order, source: User,
            products: List[ProductVariant]) -> models.Model:
        raise NotImplementedError

    @classmethod
    def draft_removed_products(
            cls, *,
            order: Order, source: User,
            products: List[ProductVariant]) -> models.Model:
        raise NotImplementedError

    @classmethod
    def placed_event(
            cls, order: Order, source: User, from_draft=False) -> models.Model:
        event_type = (
            OrderEvents.PLACED_FROM_DRAFT if from_draft else OrderEvents.PLACED
        )
        return cls(
            order=order, type=event_type.value, user=source)

    @classmethod
    def draft_oversold_items_event(
            cls, *,
            order: Order, source: User,
            oversold_items: List[str]) -> models.Model:
        return cls(
            order=order, type=OrderEvents.OVERSOLD_ITEMS.value,
            user=source,
            parameters={
                'oversold_items': oversold_items})

    @classmethod
    def cancelled_event(
            cls, *,
            order: Order, source: User) -> models.Model:
        return cls(
            order=order, type=OrderEvents.CANCELED.value,
            user=source)

    @classmethod
    def manually_marked_as_paid_event(
            cls, *,
            order: Order, source: User) -> models.Model:
        return cls(
            order=order, type=OrderEvents.ORDER_MARKED_AS_PAID.value,
            user=source)

    @classmethod
    def fully_paid_event_event(cls, *, order: Order) -> models.Model:
        return cls(order=order)

    @staticmethod
    def _get_payment_data(
            amount: Union[Money, None], payment: Payment) -> Dict:
        return {
            'parameters': {
                'amount': amount,
                'payment_id': payment.token,
                'payment_gateway': payment.gateway}}

    @classmethod
    def payment_captured_event(
            cls, *,
            order: Order, source: User,
            amount: Money, payment: Payment) -> models.Model:
        return cls(
            order=order, type=OrderEvents.PAYMENT_CAPTURED.value,
            user=source, **cls._get_payment_data(amount, payment))

    @classmethod
    def payment_refunded_event(
            cls, *,
            order: Order, source: User,
            amount: Money, payment: Payment) -> models.Model:
        return cls(
            order=order, type=OrderEvents.PAYMENT_CAPTURED.value,
            user=source, **cls._get_payment_data(amount, payment))

    @classmethod
    def payment_voided_event(
            cls, *,
            order: Order, source: User, payment: Payment) -> models.Model:
        return cls(
            order=order, type=OrderEvents.PAYMENT_CAPTURED.value,
            user=source, **cls._get_payment_data(None, payment))

    @classmethod
    def payment_failed_event(
            cls, *,
            order: Order, source: User) -> models.Model:
        raise NotImplementedError

    @classmethod
    def fulfillment_canceled_event(
            cls, *,
            order: Order, source: User,
            fulfillment: Fulfillment) -> models.Model:
        return cls(
            order=order, type=OrderEvents.FULFILLMENT_CANCELED.value,
            user=source,
            parameters={'composed_id': fulfillment.composed_id})

    @classmethod
    def fulfillment_restocked_items_event(
            cls, *,
            order: Order, source: User,
            fulfillment: Union[Order, Fulfillment]) -> models.Model:
        return cls(
            order=order, type=OrderEvents.FULFILLMENT_RESTOCKED_ITEMS.value,
            user=source,
            parameters={
                'quantity': fulfillment.get_total_quantity()})

    @classmethod
    def fulfillment_fulfilled_items_event(
            cls, *,
            order: Order, source: User,
            quantities: List[int],
            order_lines: List[OrderLine]) -> models.Model:
        return cls(
            order=order, type=OrderEvents.FULFILLMENT_FULFILLED_ITEMS.value,
            user=source,
            parameters={
                'fulfilled_items': [{
                    'quantity': quantity,
                    'item': str(line)
                } for quantity, line in zip(quantities, order_lines)]})

    @classmethod
    def fulfillment_tracking_updated_event(
            cls, *,
            order: Order, source: User,
            tracking_number: str,
            fulfillment: Fulfillment) -> models.Model:
        return cls(
            order=order, type=OrderEvents.TRACKING_UPDATED.value,
            user=source,
            parameters={
                'tracking_number': tracking_number,
                'fulfillment': fulfillment.composed_id})

    @classmethod
    def note_added_event(
            cls, *,
            order: Order, source: User, message: str) -> models.Model:
        return cls(
            order=order, type=OrderEvents.NOTE_ADDED.value,
            user=source,
            parameters={
                'message': message})

    @classmethod
    def updated_address_event(
            cls, *,
            order: Order, source: User, address: Address) -> models.Model:
        return cls(
            order=order, type=OrderEvents.UPDATED_ADDRESS.value,
            user=source,
            parameters={
                'new_address': str(address)})
