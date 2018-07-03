import graphene
from django.utils.translation import npgettext_lazy, pgettext_lazy
from graphql_jwt.decorators import permission_required

from saleor.graphql.core.mutations import BaseMutation, ModelMutation
from saleor.graphql.core.types import Error
from saleor.graphql.order.types import Fulfillment
from saleor.graphql.utils import get_node
from saleor.order import models
from saleor.order.utils import cancel_fulfillment


class FulfillmentLineInput(graphene.InputObjectType):
    order_line_id = graphene.ID(description='The ID of the order line.')
    quantity = graphene.Int(
        description='The number of line item(s) to be fulfiled.')


class FulfillmentCreateInput(graphene.InputObjectType):
    order = graphene.ID(description='ID of the order to be fulfilled.')
    tracking_number = graphene.String(
        description='Fulfillment tracking number')
    notify_customer = graphene.Boolean(description='Is customer notified.')
    lines = graphene.List(
        FulfillmentLineInput, description='Item line to be fulfilled.')


class FulfillmentUpdateInput(graphene.InputObjectType):
    tracking_number = graphene.String(
        description='Fulfillment tracking number')
    notify_customer = graphene.Boolean(description='Is customer notified.')


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

    fulfillment = graphene.Field(
        Fulfillment, description='released fulfillment.')

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
