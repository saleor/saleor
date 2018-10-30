from textwrap import dedent

import graphene
from django.utils.translation import npgettext_lazy, pgettext_lazy
from graphql_jwt.decorators import permission_required

from ....dashboard.order.utils import fulfill_order_line
from ....order import OrderEvents, OrderEventsEmails, models
from ....order.emails import send_fulfillment_confirmation
from ....order.utils import cancel_fulfillment, update_order_status
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
        description='The number of line item(s) to be fulfiled.')


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

    @classmethod
    def clean_lines(cls, order_lines, quantities, errors):
        for order_line, quantity in zip(order_lines, quantities):
            if quantity <= 0:
                cls.add_error(
                    errors, order_line,
                    'Quantity must be larger than 0.')
            elif quantity > order_line.quantity_unfulfilled:
                msg = npgettext_lazy(
                    'Fulfill order line mutation error',
                    'Only %(quantity)d item remaining to fulfill.',
                    'Only %(quantity)d items remaining to fulfill.',
                    'quantity') % {
                        'quantity': order_line.quantity_unfulfilled,
                        'order_line': order_line}
                cls.add_error(errors, order_line, msg)
        return errors

    @classmethod
    def clean_input(cls, input, errors):
        lines = input['lines']
        quantities = [line['quantity'] for line in lines]
        lines_ids = [line['order_line_id'] for line in lines]
        order_lines = cls.get_nodes_or_error(
            lines_ids, errors, 'lines', OrderLine)

        cls.clean_lines(order_lines, quantities, errors)
        if errors:
            return cls(errors=errors)
        input['order_lines'] = order_lines
        input['quantities'] = quantities
        return input

    @classmethod
    def save(cls, user, fulfillment, order, cleaned_input):
        fulfillment.save()
        order_lines = cleaned_input.get('order_lines')
        quantities = cleaned_input.get('quantities')
        fulfillment_lines = []
        for order_line, quantity in zip(order_lines, quantities):
            fulfill_order_line(order_line, quantity)
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
        if cleaned_input.get('notify_customer'):
            send_fulfillment_confirmation_to_customer(
                order, fulfillment, user)
        return fulfillment

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, order, input):
        errors = []
        order = cls.get_node_or_error(
            info, order, errors, 'order', Order)
        if errors:
            return cls(errors=errors)
        fulfillment = models.Fulfillment(
            tracking_number=input.pop('tracking_number', None) or '',
            order=order)
        cleaned_input = cls.clean_input(input, errors)
        if errors:
            return cls(errors=errors)
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

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, id, input):
        errors = []
        fulfillment = cls.get_node_or_error(
            info, id, errors, 'id', Fulfillment)
        if errors:
            return cls(errors=errors)
        tracking_number = input.get('tracking_number') or ''
        fulfillment.tracking_number = tracking_number
        fulfillment.save()
        order = fulfillment.order
        order.events.create(
            parameters={
                'tracking_numner': tracking_number,
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
        description = dedent("""Cancels existing fulfillment
        and optionally restocks items.""")

    @classmethod
    @permission_required('order.manage_orders')
    def mutate(cls, root, info, id, input):
        errors = []
        restock = input.get('restock')
        fulfillment = cls.get_node_or_error(
            info, id, errors, 'id', Fulfillment)
        if fulfillment:
            order = fulfillment.order
            if not fulfillment.can_edit():
                err_msg = pgettext_lazy(
                    'Cancel fulfillment mutation error',
                    'This fulfillment can\'t be canceled')
                cls.add_error(errors, 'fulfillment', err_msg)

        if errors:
            return cls(errors=errors)

        cancel_fulfillment(fulfillment, restock)
        if restock:
            order.events.create(
                parameters={'quantity': fulfillment.get_total_quantity()},
                type=OrderEvents.FULFILLMENT_RESTOCKED_ITEMS.value,
                user=info.context.user)
        else:
            order.events.create(
                parameters={'composed_id': fulfillment.composed_id},
                type=OrderEvents.FULFILLMENT_CANCELED.value,
                user=info.context.user)
        return FulfillmentCancel(fulfillment=fulfillment, order=order)
