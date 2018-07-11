import graphene
from django.utils.translation import npgettext_lazy, pgettext_lazy
from graphql_jwt.decorators import permission_required

from ....dashboard.order.utils import fulfill_order_line
from ....graphql.core.mutations import BaseMutation, ModelMutation
from ....graphql.core.types import Error
from ....graphql.order.types import Fulfillment
from ....graphql.utils import get_node, get_nodes
from ....order import models
from ....order.emails import send_fulfillment_confirmation
from ....order.utils import cancel_fulfillment, update_order_status
from ..types import OrderLine


def clean_lines_quantities(order_lines, quantities):
    errors = []
    for order_line, quantity in zip(order_lines, quantities):
        if quantity > order_line.quantity_unfulfilled:
            msg = npgettext_lazy(
                'Fulfill order line mutation error',
                '%(quantity)d item remaining to fulfill.',
                '%(quantity)d items remaining to fulfill.',
                'quantity') % {
                    'quantity': order_line.quantity_unfulfilled,
                    'order_line': order_line}
            errors.append((order_line.variant.name, msg))
    return errors


class FulfillmentLineInput(graphene.InputObjectType):
    order_line_id = graphene.ID(description='The ID of the order line.')
    quantity = graphene.Int(
        description='The number of line item(s) to be fulfiled.')


class FulfillmentCreateInput(graphene.InputObjectType):
    order = graphene.ID(description='ID of the order to be fulfilled.')
    tracking_number = graphene.String(
        description='Fulfillment tracking number')
    notify_customer = graphene.Boolean(
        description='If true, send an email notification to the customer.')
    lines = graphene.List(
        FulfillmentLineInput, description='Item line to be fulfilled.')


class FulfillmentUpdateInput(graphene.InputObjectType):
    tracking_number = graphene.String(
        description='Fulfillment tracking number')
    notify_customer = graphene.Boolean(
        description='If true, send an email notification to the customer.')


class FulfillmentCancelInput(graphene.InputObjectType):
    restock = graphene.Boolean(description='Whether item lines are restocked.')


class FulfillmentCreate(ModelMutation):
    class Arguments:
        input = FulfillmentCreateInput(
            required=True,
            description='Fields required to create an fulfillment.')

    class Meta:
        description = 'Creates a new fulfillment for an order.'
        model = models.Fulfillment

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        lines = input.pop('lines', None)
        cleaned_input = super().clean_input(info, instance, input, errors)
        if lines:
            lines_ids = [line.get('order_line_id') for line in lines]
            quantities = [line.get('quantity') for line in lines]
            order_lines = get_nodes(
                ids=lines_ids, graphene_type=OrderLine)
            line_errors = clean_lines_quantities(order_lines, quantities)
            if line_errors:
                for err in line_errors:
                    cls.add_error(errors, field=err[0], message=err[1])
            else:
                cleaned_input['order_lines'] = order_lines
                cleaned_input['quantities'] = quantities
        return cleaned_input

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('order.edit_order')

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        instance.order = cleaned_data.get('order') or instance.order
        return super().construct_instance(instance, cleaned_data)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        order_lines = cleaned_input.get('order_lines')
        quantities = cleaned_input.get('quantities')
        super().save(info, instance, cleaned_input)
        order = instance.order
        if order_lines and quantities:
            quantity_fulfilled = 0
            lines_to_fulfill = [
                (order_line, quantity) for order_line, quantity
                in zip(order_lines, quantities) if quantity > 0]
            for line in lines_to_fulfill:
                order_line = line[0]
                quantity = line[1]
                fulfill_order_line(order_line, quantity)
                quantity_fulfilled += quantity
            fulfillment_lines = [
                models.FulfillmentLine(
                    order_line=line[0],
                    fulfillment=instance,
                    quantity=line[1]) for line in lines_to_fulfill]
            models.FulfillmentLine.objects.bulk_create(fulfillment_lines)
            update_order_status(order)
            msg = npgettext_lazy(
                'Dashboard message related to an order',
                'Fulfilled %(quantity_fulfilled)d item',
                'Fulfilled %(quantity_fulfilled)d items',
                'quantity_fulfilled') % {
                    'quantity_fulfilled': quantity_fulfilled}
            order.history.create(content=msg, user=info.context.user)
        super().save(info, instance, cleaned_input)

        if cleaned_input.get('notify_customer'):
            send_fulfillment_confirmation.delay(order.pk, instance.pk)
            send_mail_msg = pgettext_lazy(
                'Dashboard message related to an order',
                'Shipping confirmation email was sent to user'
                '(%(email)s)') % {'email': order.get_user_current_email()}
            order.history.create(content=send_mail_msg, user=info.context.user)


class FulfillmentUpdate(FulfillmentCreate):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an fulfillment to update.')
        input = FulfillmentUpdateInput(
            required=True,
            description='Fields required to update an fulfillment.')

    class Meta:
        description = 'Updates a fulfillment for an order.'
        model = models.Fulfillment


class FulfillmentCancel(BaseMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an fulfillment to cancel.')
        input = FulfillmentCancelInput(
            required=True,
            description='Fields required to cancel an fulfillment.')

    class Meta:
        description = """Cancels existing fulfillment
        and optionally restocks items."""

    fulfillment = graphene.Field(
        Fulfillment, description='A canceled fulfillment.')

    @classmethod
    @permission_required('order.edit_order')
    def mutate(cls, root, info, id, input):
        restock = input.get('restock')
        fulfillment = get_node(info, id, only_type=Fulfillment)
        order = fulfillment.order
        errors = []
        if not fulfillment.can_edit():
            errors.append(
                Error(
                    field='fulfillment',
                    message=pgettext_lazy(
                        'Cancel fulfillment mutation error',
                        'This fulfillment can\'t be canceled')))
        if errors:
            return cls(errors=errors)
        cancel_fulfillment(fulfillment, restock)
        if restock:
            msg = npgettext_lazy(
                'Dashboard message',
                'Restocked %(quantity)d item',
                'Restocked %(quantity)d items',
                'quantity') % {'quantity': fulfillment.get_total_quantity()}
        else:
            msg = pgettext_lazy(
                'Dashboard message',
                'Fulfillment #%(fulfillment)s canceled') % {
                    'fulfillment': fulfillment.composed_id}
        order.history.create(content=msg, user=info.context.user)
        return FulfillmentCancel(fulfillment=fulfillment)
