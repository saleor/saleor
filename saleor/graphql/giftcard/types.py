import graphene
from graphql_jwt.decorators import permission_required

from ...giftcard import models
from ..core.connection import CountableDjangoObjectType


class GiftCard(CountableDjangoObjectType):
    display_code = graphene.String(
        description="Code in format with allows displaying in a user interface."
    )
    code = graphene.String(description="Gift card code.")
    user = graphene.Field(
        "saleor.graphql.account.types.User",
        description="The customer who bought a gift card.",
    )

    class Meta:
        description = """
        A gift card is a prepaid electronic payment card accepted in stores.
        They can be used during checkout by providing a valid gift
        card codes. """
        only_fields = [
            "user",
            "code",
            "created",
            "start_date",
            "end_date",
            "last_used_on",
            "is_active",
            "initial_balance",
            "current_balance",
        ]
        interfaces = [graphene.relay.Node]
        model = models.GiftCard

    @staticmethod
    def resolve_display_code(root: models.GiftCard, *_args, **_kwargs):
        return root.display_code

    @staticmethod
    @permission_required("giftcard.manage_gift_card")
    def resolve_user(root: models.GiftCard, *_args, **_kwargs):
        return root.user

    @staticmethod
    def resolve_code(root: models.GiftCard, info, **_kwargs):
        viewer = info.context.user
        # Staff user has access to show gift card code only for gift card without user.
        if viewer.has_perm("giftcard.manage_gift_card") and not root.user:
            return root.code
        # Only user associated with a gift card can see gift card code.
        if viewer == root.user:
            return root.code
        return None
