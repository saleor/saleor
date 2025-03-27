import datetime
from decimal import Decimal

import graphene
import prices

from ...core.anonymize import obfuscate_email
from ...core.exceptions import PermissionDenied
from ...giftcard import GiftCardEvents, models
from ...permission.auth_filters import AuthorizationFilters
from ...permission.enums import AccountPermissions, AppPermission, GiftcardPermissions
from ..account.dataloaders import UserByUserIdLoader
from ..account.utils import (
    check_is_owner_or_has_one_of_perms,
    is_owner_or_has_one_of_perms,
)
from ..app.dataloaders import AppByIdLoader
from ..app.types import App
from ..channel import ChannelContext
from ..channel.dataloaders import ChannelByIdLoader
from ..core.connection import CountableConnection
from ..core.context import get_database_connection_name
from ..core.descriptions import DEFAULT_DEPRECATION_REASON
from ..core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ..core.fields import PermissionsField
from ..core.scalars import Date, DateTime
from ..core.tracing import traced_resolver
from ..core.types import BaseObjectType, ModelObjectType, Money, NonNullList
from ..meta.types import ObjectWithMetadata
from ..order.dataloaders import OrderByIdLoader
from ..product.dataloaders.products import ProductByIdLoader
from ..utils import get_user_or_app_from_context
from .dataloaders import (
    GiftCardEventsByGiftCardIdLoader,
    GiftCardTagsByGiftCardIdLoader,
)
from .enums import GiftCardEventsEnum
from .filters import (
    GiftCardEventFilterInput,
    filter_events_by_orders,
    filter_events_by_type,
)


class GiftCardEventBalance(BaseObjectType):
    initial_balance = graphene.Field(
        Money,
        description="Initial balance of the gift card.",
    )
    current_balance = graphene.Field(
        Money,
        description="Current balance of the gift card.",
        required=True,
    )
    old_initial_balance = graphene.Field(
        Money,
        description="Previous initial balance of the gift card.",
    )
    old_current_balance = graphene.Field(
        Money,
        description="Previous current balance of the gift card.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_GIFT_CARDS


class GiftCardEvent(ModelObjectType[models.GiftCardEvent]):
    id = graphene.GlobalID(
        required=True, description="ID of the event associated with a gift card."
    )
    date = DateTime(description="Date when event happened at in ISO 8601 format.")
    type = GiftCardEventsEnum(description="Gift card event type.")
    user = graphene.Field(
        "saleor.graphql.account.types.User",
        description=(
            "User who performed the action. Requires one of the following "
            f"permissions: {AccountPermissions.MANAGE_USERS.name}, "
            f"{AccountPermissions.MANAGE_STAFF.name}, "
            f"{AuthorizationFilters.OWNER.name}."
        ),
    )
    app = graphene.Field(
        App,
        description=(
            "App that performed the action. Requires one of the following permissions: "
            f"{AppPermission.MANAGE_APPS.name}, {AuthorizationFilters.OWNER.name}."
        ),
    )
    message = graphene.String(description="Content of the event.")
    email = graphene.String(description="Email of the customer.")
    order_id = graphene.ID(
        description="The order ID where gift card was used or bought."
    )
    order_number = graphene.String(
        description=(
            "User-friendly number of an order where gift card was used or bought."
        )
    )
    tags = NonNullList(
        graphene.String,
        description="The list of gift card tags.",
    )
    old_tags = NonNullList(
        graphene.String,
        description="The list of old gift card tags.",
    )
    balance = graphene.Field(GiftCardEventBalance, description="The gift card balance.")
    expiry_date = Date(description="The gift card expiry date.")
    old_expiry_date = Date(description="Previous gift card expiry date.")

    class Meta:
        description = "History log of the gift card."
        model = models.GiftCardEvent
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_user(root: models.GiftCardEvent, info):
        def _resolve_user(event_user):
            requester = get_user_or_app_from_context(info.context)
            check_is_owner_or_has_one_of_perms(
                requester,
                event_user,
                AccountPermissions.MANAGE_USERS,
                AccountPermissions.MANAGE_STAFF,
            )
            return event_user

        if root.user_id is None:
            return _resolve_user(None)

        return UserByUserIdLoader(info.context).load(root.user_id).then(_resolve_user)

    @staticmethod
    def resolve_app(root: models.GiftCardEvent, info):
        def _resolve_app(app):
            requester = get_user_or_app_from_context(info.context)
            check_is_owner_or_has_one_of_perms(
                requester, app, AppPermission.MANAGE_APPS
            )
            return app

        if root.app_id is None:
            return _resolve_app(None)

        return AppByIdLoader(info.context).load(root.app_id).then(_resolve_app)

    @staticmethod
    def resolve_message(root: models.GiftCardEvent, _info):
        return root.parameters.get("message")

    @staticmethod
    def resolve_email(root: models.GiftCardEvent, _info):
        return root.parameters.get("email")

    @staticmethod
    def resolve_order_id(root: models.GiftCardEvent, info):
        order_id = root.order_id
        return graphene.Node.to_global_id("Order", order_id) if order_id else None

    @staticmethod
    def resolve_order_number(root: models.GiftCardEvent, info):
        def _resolve_order_number(order):
            return order.number

        if not root.order_id:
            return None

        return (
            OrderByIdLoader(info.context)
            .load(root.order_id)
            .then(_resolve_order_number)
        )

    @staticmethod
    def resolve_tags(root: models.GiftCardEvent, _info):
        return root.parameters.get("tags")

    @staticmethod
    def resolve_old_tags(root: models.GiftCardEvent, _info):
        return root.parameters.get("old_tags")

    @staticmethod
    @traced_resolver
    def resolve_balance(root: models.GiftCardEvent, _info):
        balance = root.parameters.get("balance")
        if balance is None:
            return None
        currency = balance["currency"]
        balance_data = {}
        for field in [
            "initial_balance",
            "old_initial_balance",
            "current_balance",
            "old_current_balance",
        ]:
            amount = balance.get(field)
            if amount is not None:
                balance_data[field] = prices.Money(Decimal(amount), currency)

        return GiftCardEventBalance(**balance_data)

    @staticmethod
    def resolve_expiry_date(root: models.GiftCardEvent, _info):
        expiry_date = root.parameters.get("expiry_date")
        return (
            datetime.datetime.strptime(expiry_date, "%Y-%m-%d").replace(
                tzinfo=datetime.UTC
            )
            if expiry_date
            else None
        )

    @staticmethod
    def resolve_old_expiry_date(root: models.GiftCardEvent, _info):
        expiry_date = root.parameters.get("old_expiry_date")
        return (
            datetime.datetime.strptime(expiry_date, "%Y-%m-%d").replace(
                tzinfo=datetime.UTC
            )
            if expiry_date
            else None
        )


class GiftCardTag(ModelObjectType[models.GiftCardTag]):
    id = graphene.GlobalID(
        required=True, description="ID of the tag associated with a gift card."
    )
    name = graphene.String(
        required=True, description="Name of the tag associated with a gift card."
    )

    class Meta:
        description = "The gift card tag."
        model = models.GiftCardTag
        interfaces = [graphene.relay.Node]


class GiftCard(ModelObjectType[models.GiftCard]):
    id = graphene.GlobalID(required=True, description="ID of the gift card.")
    display_code = graphene.String(
        description="Code in format which allows displaying in a user interface.",
        required=True,
    )
    last_4_code_chars = graphene.String(
        description="Last 4 characters of gift card code.",
        required=True,
    )
    code = graphene.String(
        description=(
            "Gift card code. It can be fetched both by a staff member with "
            f"'{GiftcardPermissions.MANAGE_GIFT_CARD.name}' when gift card "
            "hasn't been used yet or a user who bought or issued the gift card."
            + "\n\nRequires one of the following permissions: "
            f"{GiftcardPermissions.MANAGE_GIFT_CARD.name}, "
            f"{AuthorizationFilters.OWNER.name}."
        ),
        required=True,
    )
    created = DateTime(
        required=True, description="Date and time when gift card was created."
    )
    created_by = graphene.Field(
        "saleor.graphql.account.types.User",
        description="The user who bought or issued a gift card.",
    )
    used_by = graphene.Field(
        "saleor.graphql.account.types.User",
        description="The customer who used a gift card.",
        deprecation_reason=DEFAULT_DEPRECATION_REASON,
    )
    created_by_email = graphene.String(
        required=False,
        description=(
            "Email address of the user who bought or issued gift card."
            + "\n\nRequires one of the following permissions: "
            f"{AccountPermissions.MANAGE_USERS.name}, "
            f"{AuthorizationFilters.OWNER.name}."
        ),
    )
    used_by_email = graphene.String(
        required=False,
        description="Email address of the customer who used a gift card.",
        deprecation_reason=DEFAULT_DEPRECATION_REASON,
    )
    last_used_on = DateTime(description="Date and time when gift card was last used.")
    expiry_date = Date(description="Expiry date of the gift card.")
    app = graphene.Field(
        App,
        description=(
            "App which created the gift card."
            + "\n\nRequires one of the following permissions: "
            f"{AppPermission.MANAGE_APPS.name}, {AuthorizationFilters.OWNER.name}."
        ),
    )
    product = graphene.Field(
        "saleor.graphql.product.types.products.Product",
        description="Related gift card product.",
    )
    events = PermissionsField(
        NonNullList(GiftCardEvent),
        filter=GiftCardEventFilterInput(
            description="Filtering options for gift card events."
        ),
        description="List of events associated with the gift card.",
        required=True,
        permissions=[
            GiftcardPermissions.MANAGE_GIFT_CARD,
        ],
    )
    tags = PermissionsField(
        NonNullList(GiftCardTag),
        description="The gift card tag.",
        required=True,
        permissions=[
            GiftcardPermissions.MANAGE_GIFT_CARD,
        ],
    )
    bought_in_channel = graphene.String(
        description="Slug of the channel where the gift card was bought.",
        required=False,
    )
    is_active = graphene.Boolean(required=True)
    initial_balance = graphene.Field(Money, required=True)
    current_balance = graphene.Field(Money, required=True)

    # DEPRECATED
    user = graphene.Field(
        "saleor.graphql.account.types.User",
        description="The customer who bought a gift card.",
        deprecation_reason="Use `createdBy` field instead.",
    )
    end_date = DateTime(
        description="End date of gift card.",
        deprecation_reason="Use `expiryDate` field instead.",
    )
    start_date = DateTime(
        description="Start date of gift card.",
        deprecation_reason=DEFAULT_DEPRECATION_REASON,
    )

    class Meta:
        description = (
            "A gift card is a prepaid electronic payment card accepted in stores. They "
            "can be used during checkout by providing a valid gift card codes."
        )
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.GiftCard

    @staticmethod
    def resolve_created(root: models.GiftCard, _info):
        return root.created_at

    @staticmethod
    def resolve_last_4_code_chars(root: models.GiftCard, _info):
        return root.display_code

    @staticmethod
    def resolve_code(root: models.GiftCard, info):
        def _resolve_code(user):
            # Gift card code can be fetched by the staff user and app
            # with manage gift card permission and by the card owner.
            if requestor := get_user_or_app_from_context(info.context):
                requestor_is_an_owner = user and requestor == user
                if requestor_is_an_owner or requestor.has_perm(
                    GiftcardPermissions.MANAGE_GIFT_CARD
                ):
                    return root.code

            return PermissionDenied(
                permissions=[
                    AuthorizationFilters.OWNER,
                    GiftcardPermissions.MANAGE_GIFT_CARD,
                ]
            )

        if root.used_by_id is None:
            return _resolve_code(None)

        return (
            UserByUserIdLoader(info.context).load(root.used_by_id).then(_resolve_code)
        )

    @staticmethod
    def resolve_created_by(root: models.GiftCard, info):
        def _resolve_created_by(user):
            requestor = get_user_or_app_from_context(info.context)
            check_is_owner_or_has_one_of_perms(
                requestor, user, AccountPermissions.MANAGE_USERS
            )
            return user

        if root.created_by_id is None:
            return _resolve_created_by(None)

        return UserByUserIdLoader(info.context).load(root.created_by_id)

    @staticmethod
    def resolve_used_by(root: models.GiftCard, info):
        def _resolve_used_by(user):
            requestor = get_user_or_app_from_context(info.context)
            if is_owner_or_has_one_of_perms(
                requestor, user, AccountPermissions.MANAGE_USERS
            ):
                return user
            return None

        if not root.used_by_id:
            return _resolve_used_by(None)

        return (
            UserByUserIdLoader(info.context)
            .load(root.used_by_id)
            .then(_resolve_used_by)
        )

    @staticmethod
    def resolve_created_by_email(root: models.GiftCard, info):
        def _resolve_created_by_email(user):
            requester = get_user_or_app_from_context(info.context)
            if is_owner_or_has_one_of_perms(
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
    def resolve_used_by_email(root: models.GiftCard, info):
        def _resolve_used_by_email(user):
            requester = get_user_or_app_from_context(info.context)
            if is_owner_or_has_one_of_perms(
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
    def resolve_app(root: models.GiftCard, info):
        def _resolve_app(app):
            requester = get_user_or_app_from_context(info.context)
            check_is_owner_or_has_one_of_perms(
                requester, app, AppPermission.MANAGE_APPS
            )
            return app

        if root.app_id is None:
            return _resolve_app(None)

        return AppByIdLoader(info.context).load(root.app_id).then(_resolve_app)

    @staticmethod
    def resolve_product(root: models.GiftCard, info):
        if root.product_id is None:
            return None
        product = ProductByIdLoader(info.context).load(root.product_id)
        return product.then(
            lambda product: ChannelContext(node=product, channel_slug=None)
        )

    @staticmethod
    def resolve_events(root: models.GiftCard, info, **kwargs):
        def filter_events(events):
            event_filter = kwargs.get("filter", {})
            if event_type_value := event_filter.get("type"):
                events = filter_events_by_type(events, event_type_value)
            if orders_value := event_filter.get("orders"):
                events = filter_events_by_orders(
                    events,
                    orders_value,
                    database_connection_name=get_database_connection_name(
                        info.context.allow_replica
                    ),
                )
            return events

        return (
            GiftCardEventsByGiftCardIdLoader(info.context)
            .load(root.id)
            .then(filter_events)
        )

    @staticmethod
    def resolve_tags(root: models.GiftCard, info):
        return GiftCardTagsByGiftCardIdLoader(info.context).load(root.id)

    @staticmethod
    @traced_resolver
    def resolve_bought_in_channel(root: models.GiftCard, info):
        def with_bought_event(events):
            bought_event = None
            for event in events:
                if event.type == GiftCardEvents.BOUGHT:
                    bought_event = event
                    break

            if bought_event is None:
                return None

            def with_order(order):
                if not order or not order.channel_id:
                    return None

                def get_channel_slug(channel):
                    return channel.slug if channel else None

                return (
                    ChannelByIdLoader(info.context)
                    .load(order.channel_id)
                    .then(get_channel_slug)
                )

            return (
                OrderByIdLoader(info.context)
                .load(bought_event.order_id)
                .then(with_order)
            )

        return (
            GiftCardEventsByGiftCardIdLoader(info.context)
            .load(root.id)
            .then(with_bought_event)
        )

    # DEPRECATED
    @staticmethod
    def resolve_user(root: models.GiftCard, info):
        def _resolve_user(user):
            requestor = get_user_or_app_from_context(info.context)
            if is_owner_or_has_one_of_perms(
                requestor, user, AccountPermissions.MANAGE_USERS
            ):
                return user
            return None

        if not root.created_by_id:
            return _resolve_user(None)

        return (
            UserByUserIdLoader(info.context)
            .load(root.created_by_id)
            .then(_resolve_user)
        )

    @staticmethod
    def resolve_end_date(root: models.GiftCard, _info):
        return root.expiry_date

    @staticmethod
    def resolve_start_date(_root: models.GiftCard, _info):
        return None


class GiftCardCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_GIFT_CARDS
        node = GiftCard


class GiftCardTagCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_GIFT_CARDS
        node = GiftCardTag
