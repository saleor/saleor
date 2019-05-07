import graphene
from django.core.exceptions import ValidationError
from django.utils.translation import npgettext_lazy, pgettext_lazy

from ....order import OrderEvents, OrderEventsEmails, models
from ....order.emails import send_fulfillment_confirmation
from ....order.utils import (
    cancel_fulfillment, fulfill_order_line, update_order_status)
from ...core.mutations import BaseMutation
from ...order.types import Fulfillment, Order
from ..types import OrderLine


def send_fulfillment_confirmation_to_customer(order, fulfillment, user):
    send_fulfillment_confirmation.delay(order.pk, fulfillment.pk)
    order.events.create(
        parameters={
            'email': order.get_user_current_email(),
            'email_type': OrderEventsEmails.FULFILLMENT.value},
        type=OrderEvents.EMAIL_SENT.value, user=user)


class FulfillmentLineInput(graphene.InputObjectType):
    order_line_id = graphene.ID(
        description='The ID of the order line.', name='orderLineId')
    quantity = graphene.Int(
        description='The number of line item(s) to be fulfilled.')


class FulfillmentCreateInput(graphene.InputObjectType):
    tracking_number = graphene.String(
        description='Fulfillment tracking number')
    notify_customer = graphene.Boolean(
        description='If true, send an email notification to the customer.')
    lines = graphene.List(
        FulfillmentLineInput, required=True,
        description='Item line to be fulfilled.')


class FulfillmentUpdateTrackingInput(graphene.InputObjectType):
    tracking_number = graphene.String(
        description='Fulfillment tracking number')
    notify_customer = graphene.Boolean(
        description='If true, send an email notification to the customer.')


class FulfillmentCancelInput(graphene.InputObjectType):
    restock = graphene.Boolean(description='Whether item lines are restocked.')


class FulfillmentCreate(BaseMutation):
    fulfillment = graphene.Field(
        Fulfillment, description='A created fulfillment.')
    order = graphene.Field(
        Order, description='Fulfilled order.')

    class Arguments:
        order = graphene.ID(
            description='ID of the order to be fulfilled.', name='order')
        input = FulfillmentCreateInput(
            required=True,
            description='Fields required to create an fulfillment.')

    class Meta:
        description = 'Creates a new fulfillment for an order.'
        permissions = ('order.manage_orders', )

    @classmethod
    def clean_lines(cls, order_lines, quantities):
        for order_line, quantity in zip(order_lines, quantities):
            if quantity > order_line.quantity_unfulfilled:
                msg = npgettext_lazy(
                    'Fulfill order line mutation error',
                    'Only %(quantity)d item remaining to fulfill: %(order_line)s.',
                    'Only %(quantity)d items remaining to fulfill: %(order_line)s.',
                    number='quantity') % {
                        'quantity': order_line.quantity_unfulfilled,
                        'order_line': order_line}
                raise ValidationError({'order_line_id': msg})

    @classmethod
    def clean_input(cls, data):
        lines = data['lines']
        quantities = [line['quantity'] for line in lines]
        lines_ids = [line['order_line_id'] for line in lines]
        order_lines = cls.get_nodes_or_error(
            lines_ids, field='lines', only_type=OrderLine)

        cls.clean_lines(order_lines, quantities)

        if sum(quantities) <= 0:
            raise ValidationError({
                'lines': 'Total quantity must be larger than 0.'})

        data['order_lines'] = order_lines
        data['quantities'] = quantities
        return data

    @classmethod
    def save(cls, user, fulfillment, order, cleaned_input):
        fulfillment.save()
        order_lines = cleaned_input.get('order_lines')
        quantities = cleaned_input.get('quantities')
        fulfillment_lines = []
        for order_line, quantity in zip(order_lines, quantities):
            fulfill_order_line(order_line, quantity)
            if order_line.is_digital:
                order_line.variant.digital_content.urls.create(line=order_line)
            fulfillment_lines.append(
                models.FulfillmentLine(
                    order_line=order_line, fulfillment=fulfillment,
                    quantity=quantity))

        fulfillment.lines.bulk_create(fulfillment_lines)
        update_order_status(order)
        order.events.create(
            parameters={'quantity': sum(quantities)},
            type=OrderEvents.FULFILLMENT_FULFILLED_ITEMS.value,
            user=user)
        if cleaned_input.get('notify_customer', True):
            send_fulfillment_confirmation_to_customer(
                order, fulfillment, user)
        return fulfillment

    @classmethod
    def perform_mutation(cls, _root, info, order, **data):
        order = cls.get_node_or_error(
            info, order, field='order', only_type=Order)
        data = data.get('input')
        fulfillment = models.Fulfillment(
            tracking_number=data.pop('tracking_number', None) or '',
            order=order)
        cleaned_input = cls.clean_input(data)
        fulfillment = cls.save(
            info.context.user, fulfillment, order, cleaned_input)
        return FulfillmentCreate(
            fulfillment=fulfillment, order=fulfillment.order)


class FulfillmentUpdateTracking(BaseMutation):
    fulfillment = graphene.Field(
        Fulfillment, description='A fulfillment with updated tracking.')
    order = graphene.Field(
        Order, description='Order which fulfillment was updated.')

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an fulfillment to update.')
        input = FulfillmentUpdateTrackingInput(
            required=True,
            description='Fields required to update an fulfillment.')

    class Meta:
        description = 'Updates a fulfillment for an order.'
        permissions = ('order.manage_orders', )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        fulfillment = cls.get_node_or_error(
            info, data.get('id'), only_type=Fulfillment)
        tracking_number = data.get('input').get('tracking_number') or ''
        fulfillment.tracking_number = tracking_number
        fulfillment.save()
        order = fulfillment.order
        order.events.create(
            parameters={
                'tracking_number': tracking_number,
                'fulfillment': fulfillment.composed_id},
            type=OrderEvents.TRACKING_UPDATED.value,
            user=info.context.user)
        return FulfillmentUpdateTracking(fulfillment=fulfillment, order=order)


class FulfillmentCancel(BaseMutation):
    fulfillment = graphene.Field(
        Fulfillment, description='A canceled fulfillment.')
    order = graphene.Field(
        Order, description='Order which fulfillment was cancelled.')

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an fulfillment to cancel.')
        input = FulfillmentCancelInput(
            required=True,
            description='Fields required to cancel an fulfillment.')

    class Meta:
        description = """Cancels existing fulfillment
        and optionally restocks items."""
        permissions = ('order.manage_orders', )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        restock = data.get('input').get('restock')
        fulfillment = cls.get_node_or_error(
            info, data.get('id'), only_type=Fulfillment)

        if not fulfillment.can_edit():
            err_msg = pgettext_lazy(
                'Cancel fulfillment mutation error',
                'This fulfillment can\'t be canceled')
            raise ValidationError({'fulfillment': err_msg})

        order = fulfillment.order
        cancel_fulfillment(fulfillment, restock)

        # FIXME: move event creation to `cancel_fulfillment`
        if restock:
            order.events.create(
                parameters={'quantity': fulfillment.get_total_quantity()},
                type=OrderEvents.FULFILLMENT_RESTOCKED_ITEMS.value,
                user=info.context.user)
        elif order:
            order.events.create(
                parameters={'composed_id': fulfillment.composed_id},
                type=OrderEvents.FULFILLMENT_CANCELED.value,
                user=info.context.user)
        return FulfillmentCancel(fulfillment=fulfillment, order=order)
