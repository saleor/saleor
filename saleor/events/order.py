from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union

from django.contrib.auth.base_user import AbstractBaseUser

from . import OrderEvents, OrderEventsEmails
from ..account.models import Address
from ..order.models import Fulfillment, Order, OrderLine
from ..payment.models import Payment
from ..product.models import ProductVariant
from .bases import EventManager
from .models import OrderEvent

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


class OrderEventManager(EventManager):
    class Meta:
        model = OrderEvent

    def email_sent_event(
            self, *,
            order: Order, email_type: OrderEventsEmails,
            user: Optional[UserType]):

        if user is not None and user.is_anonymous:
            user = None

        return self.new_event(
            order=order, type=OrderEvents.EMAIL_SENT, user=user,
            parameters={
                'email': order.get_user_current_email(),
                'email_type': email_type})

    def email_resent_event(
            self, *,
            order: Order, email_type: OrderEventsEmails,
            user: UserType):
        raise NotImplementedError

    def draft_order_created_event(
            self, *, order: Order, user: UserType):
        return self.new_event(
            order=order, type=OrderEvents.DRAFT_CREATED, user=user)

    def draft_order_added_products_event(
            self, *,
            order: Order, user: UserType,
            order_lines: List[Tuple[int, ProductVariant]]):

        return self.new_event(
            order=order, type=OrderEvents.DRAFT_ADDED_PRODUCTS,
            user=user,
            parameters={
                'lines': _lines_per_quantity_to_str_line_list(order_lines)})

    def draft_order_removed_products_event(
            self, *,
            order: Order, user: UserType,
            order_lines: List[Tuple[int, ProductVariant]]):

        return self.new_event(
            order=order, type=OrderEvents.DRAFT_REMOVED_PRODUCTS,
            user=user,
            parameters={
                'lines': _lines_per_quantity_to_str_line_list(order_lines)})

    def order_created_event(
            self, order: Order, user: UserType,
            from_draft=False):
        event_type = (
            OrderEvents.PLACED_FROM_DRAFT if from_draft else OrderEvents.PLACED
        )

        if user.is_anonymous:
            user = None

        return self.new_event(
            order=order, type=event_type, user=user)

    def draft_order_oversold_items_event(
            self, *,
            order: Order, user: UserType,
            oversold_items: List[str]):
        return self.new_event(
            order=order, type=OrderEvents.OVERSOLD_ITEMS,
            user=user,
            parameters={
                'oversold_items': oversold_items})

    def order_canceled_event(
            self, *,
            order: Order, user: UserType):
        return self.new_event(
            order=order, type=OrderEvents.CANCELED,
            user=user)

    def order_manually_marked_as_paid_event(
            self, *,
            order: Order, user: UserType):
        return self.new_event(
            order=order, type=OrderEvents.ORDER_MARKED_AS_PAID,
            user=user)

    def order_fully_paid_event(self, *, order: Order):
        return self.new_event(order=order, type=OrderEvents.ORDER_FULLY_PAID)

    def payment_captured_event(
            self, *,
            order: Order, user: UserType,
            amount: Decimal, payment: Payment):
        return self.new_event(
            order=order, type=OrderEvents.PAYMENT_CAPTURED,
            user=user, **_get_payment_data(amount, payment))

    def payment_refunded_event(
            self, *,
            order: Order, user: UserType,
            amount: Decimal, payment: Payment):
        return self.new_event(
            order=order, type=OrderEvents.PAYMENT_REFUNDED,
            user=user, **_get_payment_data(amount, payment))

    def payment_voided_event(
            self, *,
            order: Order, user: UserType, payment: Payment):
        return self.new_event(
            order=order, type=OrderEvents.PAYMENT_VOIDED,
            user=user, **_get_payment_data(None, payment))

    def payment_failed_event(
            self, *,
            order: Order, user: UserType, message: str,
            payment: Payment):

        parameters = {'message': message}

        if payment:
            parameters.update({
                'gateway': payment.gateway,
                'payment_id': payment.token})

        return self.new_event(
            order=order, type=OrderEvents.PAYMENT_FAILED,
            user=user, parameters=parameters)

    def fulfillment_canceled_event(
            self, *,
            order: Order, user: UserType,
            fulfillment: Fulfillment):
        return self.new_event(
            order=order, type=OrderEvents.FULFILLMENT_CANCELED,
            user=user,
            parameters={'composed_id': fulfillment.composed_id})

    def fulfillment_restocked_items_event(
            self, *,
            order: Order, user: UserType,
            fulfillment: Union[Order, Fulfillment]):
        return self.new_event(
            order=order, type=OrderEvents.FULFILLMENT_RESTOCKED_ITEMS,
            user=user,
            parameters={
                'quantity': fulfillment.get_total_quantity()})

    def fulfillment_fulfilled_items_event(
            self, *,
            order: Order, user: UserType,
            quantities: List[int],
            order_lines: List[OrderLine]):
        return self.new_event(
            order=order, type=OrderEvents.FULFILLMENT_FULFILLED_ITEMS,
            user=user,
            parameters={
                'lines': _lines_per_quantity_to_str_line_list(
                    zip(quantities, order_lines))})

    def fulfillment_tracking_updated_event(
            self, *,
            order: Order, user: UserType,
            tracking_number: str,
            fulfillment: Fulfillment):
        return self.new_event(
            order=order, type=OrderEvents.TRACKING_UPDATED,
            user=user,
            parameters={
                'tracking_number': tracking_number,
                'fulfillment': fulfillment.composed_id})

    def order_note_added_event(
            self, *,
            order: Order, user: UserType, message: str):
        return self.new_event(
            order=order, type=OrderEvents.NOTE_ADDED,
            user=user,
            parameters={
                'message': message})

    def order_updated_address_event(
            self, *,
            order: Order, user: UserType, address: Address):
        return self.new_event(
            order=order, type=OrderEvents.UPDATED_ADDRESS,
            user=user,
            parameters={
                'new_address': str(address)})
