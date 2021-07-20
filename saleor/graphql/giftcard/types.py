import graphene

from ...core.exceptions import PermissionDenied
from ...core.permissions import AccountPermissions, GiftcardPermissions
from ...core.tracing import traced_resolver
from ...giftcard import models
from ..account.utils import requestor_has_access
from ..core.connection import CountableDjangoObjectType
from ..utils import get_user_or_app_from_context


class GiftCard(CountableDjangoObjectType):
    display_code = graphene.String(
        description="Code in format which allows displaying in a user interface."
    )
    code = graphene.String(description="Gift card code.")
    user = graphene.Field(
        "saleor.graphql.account.types.User",
        description="The customer who bought a gift card.",
        # TODO: Add info about using created_by instead, when updating gift card type
        deprecation_reason="Will be removed in Saleor 4.0.",
    )
    end_date = graphene.types.datetime.DateTime(
        description="End date of gift card.",
        # TODO: Add info about using expiry_date instead, when updating gift card type
        deprecation_reason=("Will be removed in Saleor 4.0."),
    )
    start_date = graphene.types.datetime.DateTime(
        description="Start date of gift card.",
        deprecation_reason=("Will be removed in Saleor 4.0."),
    )

    class Meta:
        description = (
            "A gift card is a prepaid electronic payment card accepted in stores. They "
            "can be used during checkout by providing a valid gift card codes."
        )
        only_fields = [
            "code",
            "created",
            "last_used_on",
            "is_active",
            "initial_balance",
            "current_balance",
        ]
        interfaces = [graphene.relay.Node]
        model = models.GiftCard

    @staticmethod
    @traced_resolver
    def resolve_display_code(root: models.GiftCard, *_args, **_kwargs):
        return root.display_code

    @staticmethod
    @traced_resolver
    def resolve_user(root: models.GiftCard, info):
        requestor = get_user_or_app_from_context(info.context)
        if requestor_has_access(
            requestor, root.created_by, AccountPermissions.MANAGE_USERS
        ):
            return root.created_by
        raise PermissionDenied()

    @staticmethod
    @traced_resolver
    def resolve_code(root: models.GiftCard, info, **_kwargs):
        user = info.context.user
        # Staff user has access to show gift card code only for gift card without user.
        if user.has_perm(GiftcardPermissions.MANAGE_GIFT_CARD) and not root.created_by:
            return root.code
        # Only user associated with a gift card can see gift card code.
        if user == root.created_by:
            return root.code
        return None

    @staticmethod
    def resolve_end_date(root: models.GiftCard, *_args, **_kwargs):
        return root.expiry_date

    @staticmethod
    def resolve_start_date(root: models.GiftCard, *_args, **_kwargs):
        return None
