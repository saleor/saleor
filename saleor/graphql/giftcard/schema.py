import graphene
from graphql_jwt.decorators import permission_required

from ...giftcard import models
from ..core.fields import PrefetchingConnectionField
from .types import GiftCard


class GiftCardQueries(graphene.ObjectType):
    gift_card = graphene.Field(
        GiftCard, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a gift card by ID.')
    gift_cards = PrefetchingConnectionField(
        GiftCard, description='List of gift cards')

    @permission_required('giftcard.manage_gift_card')
    def resolve_gift_card(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, GiftCard)

    @permission_required('giftcard.manage_gift_card')
    def resolve_gift_cards(self, info, **_kwargs):
        return models.GiftCard.objects.all()
