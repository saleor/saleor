import graphene

from ...core.anonymize import obfuscate_email
from ...core.exceptions import PermissionDenied
from ...core.permissions import AccountPermissions, AppPermission, GiftcardPermissions
from ...core.tracing import traced_resolver
from ...giftcard import models
from ..account.dataloaders import UserByUserIdLoader
from ..account.utils import requestor_has_access
from ..app.dataloaders import AppByIdLoader
from ..app.types import App
from ..core.connection import CountableDjangoObjectType
from ..core.types.common import TimePeriod
from ..meta.types import ObjectWithMetadata
from ..product.dataloaders.products import ProductByIdLoader
from ..utils import get_user_or_app_from_context
from .enums import GiftCardExpiryTypeEnum


class GiftCard(CountableDjangoObjectType):
    display_code = graphene.String(
        description="Code in format which allows displaying in a user interface."
    )
    code = graphene.String(
        description=(
            "Gift card code. "
            "Can be fetched by staff member with manage gift card permission when "
            "gift card wasn't used yet and by the gift card owner."
        ),
        required=True,
    )
    created_by = graphene.Field(
        "saleor.graphql.account.types.User",
        description="The user who bought or issued a gift card.",
    )
    used_by = graphene.Field(
        "saleor.graphql.account.types.User",
        description="The customer who used a gift card.",
    )
    created_by_email = graphene.String(
        required=False,
        description="Email address of the user who bought or issued gift card.",
    )
    used_by_email = graphene.String(
        required=False,
        description="Email address of the customer who used a gift card.",
    )
    app = graphene.Field(
        App,
        description="App which created the gift card.",
    )
    expiry_type = GiftCardExpiryTypeEnum(description="The gift card expiry type.")
    expiry_period = graphene.Field(
        TimePeriod, description="The gift card expiry period.", required=False
    )
    product = graphene.Field(
        "saleor.graphql.product.types.products.Product",
        description="Related gift card product.",
    )

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
            "start_date",
            "last_used_on",
            "is_active",
            "initial_balance",
            "current_balance",
            "expiry_date",
            "expiry_type",
            "tag",
        ]
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.GiftCard

    @staticmethod
    @traced_resolver
    def resolve_display_code(root: models.GiftCard, *_args, **_kwargs):
        return root.display_code

    @staticmethod
    @traced_resolver
    def resolve_code(root: models.GiftCard, info, **_kwargs):
        requestor = get_user_or_app_from_context(info.context)
        # Gift card code can be fetched by the staff user and app
        # with manage gift card permission and by the card owner.
        if (
            not root.used_by_email
            and requestor.has_perm(GiftcardPermissions.MANAGE_GIFT_CARD)
        ) or requestor == root.used_by:
            return root.code
        return PermissionDenied()

    @staticmethod
    @traced_resolver
    def resolve_created_by(root: models.GiftCard, info):
        requestor = get_user_or_app_from_context(info.context)
        if requestor_has_access(
            requestor, root.created_by, AccountPermissions.MANAGE_USERS
        ):
            return (
                UserByUserIdLoader(info.context).load(root.created_by_id)
                if root.created_by_id
                else None
            )
        raise PermissionDenied()

    @staticmethod
    @traced_resolver
    def resolve_used_by(root: models.GiftCard, info):
        requestor = get_user_or_app_from_context(info.context)
        if requestor_has_access(
            requestor, root.used_by, AccountPermissions.MANAGE_USERS
        ):
            return (
                UserByUserIdLoader(info.context).load(root.used_by_id)
                if root.used_by_id
                else None
            )
        raise PermissionDenied()

    @staticmethod
    @traced_resolver
    def resolve_created_by_email(root: models.GiftCard, info):
        def _resolve_created_by_email(user):
            requester = get_user_or_app_from_context(info.context)
            if requestor_has_access(
                requester, user, GiftcardPermissions.MANAGE_GIFT_CARD
            ):
                return user.email if user else root.created_by_email
            return obfuscate_email(user.email if user else root.created_by_email)

        if not root.created_by_id:
            return _resolve_created_by_email(None)

        return (
            UserByUserIdLoader(info.context)
            .load(root.created_by_id)
            .then(_resolve_created_by_email)
        )

    @staticmethod
    @traced_resolver
    def resolve_used_by_email(root: models.GiftCard, info):
        def _resolve_used_by_email(user):
            requester = get_user_or_app_from_context(info.context)
            if requestor_has_access(
                requester, user, GiftcardPermissions.MANAGE_GIFT_CARD
            ):
                return user.email if user else root.used_by_email
            return obfuscate_email(user.email if user else root.used_by_email)

        if not root.used_by_id:
            return _resolve_used_by_email(None)

        return (
            UserByUserIdLoader(info.context)
            .load(root.used_by_id)
            .then(_resolve_used_by_email)
        )

    @staticmethod
    @traced_resolver
    def resolve_app(root: models.GiftCard, info):
        requestor = get_user_or_app_from_context(info.context)
        if requestor_has_access(requestor, root.used_by, AppPermission.MANAGE_APPS):
            return (
                AppByIdLoader(info.context).load(root.app_id) if root.app_id else None
            )
        raise PermissionDenied()

    @staticmethod
    @traced_resolver
    def resolve_product(root: models.GiftCard, info):
        if root.product_id is None:
            return None
        return ProductByIdLoader(info.context).load(root.product_id)

    @staticmethod
    @traced_resolver
    def resolve_expiry_period(root: models.GiftCard, info):
        if root.expiry_period_type is None:
            return None
        return TimePeriod(amount=root.expiry_period, type=root.expiry_period_type)

    @staticmethod
    @traced_resolver
    def resolve_user(root: models.GiftCard, info):
        requestor = get_user_or_app_from_context(info.context)
        if requestor_has_access(
            requestor, root.created_by, AccountPermissions.MANAGE_USERS
        ):
            return (
                UserByUserIdLoader(info.context).load(root.created_by_id)
                if root.created_by_id
                else None
            )
        raise PermissionDenied()

    @staticmethod
    def resolve_end_date(root: models.GiftCard, *_args, **_kwargs):
        return root.expiry_date

    @staticmethod
    def resolve_start_date(root: models.GiftCard, *_args, **_kwargs):
        return None
