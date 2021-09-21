import datetime
from decimal import Decimal

import graphene
import prices

from ...core.anonymize import obfuscate_email
from ...core.exceptions import PermissionDenied
from ...core.permissions import AccountPermissions, AppPermission, GiftcardPermissions
from ...core.tracing import traced_resolver
from ...giftcard import GiftCardEvents, models
from ..account.dataloaders import UserByUserIdLoader
from ..account.utils import requestor_has_access
from ..app.dataloaders import AppByIdLoader
from ..app.types import App
from ..channel import ChannelContext
from ..channel.dataloaders import ChannelByIdLoader
from ..core.connection import CountableDjangoObjectType
from ..core.descriptions import ADDED_IN_31, DEPRECATED_IN_3X_FIELD
from ..core.types.money import Money
from ..decorators import permission_required
from ..meta.types import ObjectWithMetadata
from ..order.dataloaders import OrderByIdLoader
from ..product.dataloaders.products import ProductByIdLoader
from ..utils import get_user_or_app_from_context
from .dataloaders import GiftCardEventsByGiftCardIdLoader
from .enums import GiftCardEventsEnum
from .filters import (
    GiftCardEventFilterInput,
    filter_events_by_orders,
    filter_events_by_type,
)


class GiftCardEventBalance(graphene.ObjectType):
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


class GiftCardEvent(CountableDjangoObjectType):
    date = graphene.types.datetime.DateTime(
        description="Date when event happened at in ISO 8601 format."
    )
    type = GiftCardEventsEnum(description="Gift card event type.")
    user = graphene.Field(
        "saleor.graphql.account.types.User",
        description="User who performed the action.",
    )
    app = graphene.Field(App, description="App that performed the action.")
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
    tag = graphene.String(description="The gift card tag.")
    old_tag = graphene.String(description="Old gift card tag.")
    balance = graphene.Field(GiftCardEventBalance, description="The gift card balance.")
    expiry_date = graphene.types.datetime.Date(description="The gift card expiry date.")
    old_expiry_date = graphene.types.datetime.Date(
        description="Previous gift card expiry date."
    )

    class Meta:
        description = f"{ADDED_IN_31} History log of the gift card."
        model = models.GiftCardEvent
        interfaces = [graphene.relay.Node]
        only_fields = ["id"]

    @staticmethod
    def resolve_user(root: models.GiftCardEvent, info):
        def _resolve_user(event_user):
            requester = get_user_or_app_from_context(info.context)
            if (
                requester == event_user
                or requester.has_perm(AccountPermissions.MANAGE_USERS)
                or requester.has_perm(AccountPermissions.MANAGE_STAFF)
            ):
                return event_user
            return PermissionDenied()

        if root.user_id is None:
            return _resolve_user(None)

        return UserByUserIdLoader(info.context).load(root.user_id).then(_resolve_user)

    @staticmethod
    def resolve_app(root: models.GiftCardEvent, info):
        def _resolve_app(app):
            requester = get_user_or_app_from_context(info.context)
            if requester == app or requester.has_perm(AppPermission.MANAGE_APPS):
                return app
            return PermissionDenied()

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
        order_id = root.parameters.get("order_id")
        return graphene.Node.to_global_id("Order", order_id) if order_id else None

    @staticmethod
    def resolve_order_number(root: models.GiftCardEvent, info):
        order_id = root.parameters.get("order_id")
        return str(order_id) if order_id else None

    @staticmethod
    def resolve_tag(root: models.GiftCardEvent, _info):
        return root.parameters.get("tag")

    @staticmethod
    def resolve_old_tag(root: models.GiftCardEvent, _info):
        return root.parameters.get("old_tag")

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
            datetime.datetime.strptime(expiry_date, "%Y-%m-%d") if expiry_date else None
        )

    @staticmethod
    def resolve_old_expiry_date(root: models.GiftCardEvent, _info):
        expiry_date = root.parameters.get("old_expiry_date")
        return (
            datetime.datetime.strptime(expiry_date, "%Y-%m-%d") if expiry_date else None
        )


class GiftCard(CountableDjangoObjectType):
    display_code = graphene.String(
        description="Code in format which allows displaying in a user interface.",
        required=True,
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
        description=f"{ADDED_IN_31} The user who bought or issued a gift card.",
    )
    used_by = graphene.Field(
        "saleor.graphql.account.types.User",
        description=f"{ADDED_IN_31} The customer who used a gift card.",
    )
    created_by_email = graphene.String(
        required=False,
        description=(
            f"{ADDED_IN_31} Email address of the user who bought or issued gift card."
        ),
    )
    used_by_email = graphene.String(
        required=False,
        description=(
            f"{ADDED_IN_31} Email address of the customer who used a gift card."
        ),
    )
    app = graphene.Field(
        App,
        description=f"{ADDED_IN_31} App which created the gift card.",
    )
    product = graphene.Field(
        "saleor.graphql.product.types.products.Product",
        description=f"{ADDED_IN_31} Related gift card product.",
    )
    events = graphene.List(
        graphene.NonNull(GiftCardEvent),
        filter=GiftCardEventFilterInput(
            description="Filtering options for gift card events."
        ),
        description=f"{ADDED_IN_31} List of events associated with the gift card.",
        required=True,
    )
    tag = graphene.String(description=f"{ADDED_IN_31} The gift card tag.")
    bought_in_channel = graphene.String(
        description=(
            "{ADDED_IN_31} Slug of the channel where the gift card was bought."
        ),
        required=False,
    )

    # DEPRECATED
    user = graphene.Field(
        "saleor.graphql.account.types.User",
        description="The customer who bought a gift card.",
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use `createdBy` field instead.",
    )
    end_date = graphene.types.datetime.DateTime(
        description="End date of gift card.",
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use `expiryDate` field instead.",
    )
    start_date = graphene.types.datetime.DateTime(
        description="Start date of gift card.",
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD}",
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
            "tag",
        ]
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.GiftCard

    @staticmethod
    def resolve_display_code(root: models.GiftCard, *_args, **_kwargs):
        return root.display_code

    @staticmethod
    def resolve_code(root: models.GiftCard, info, **_kwargs):
        def _resolve_code(user):
            requestor = get_user_or_app_from_context(info.context)
            # Gift card code can be fetched by the staff user and app
            # with manage gift card permission and by the card owner.
            if (
                not root.used_by_email
                and requestor.has_perm(GiftcardPermissions.MANAGE_GIFT_CARD)
            ) or (user and requestor == user):
                return root.code

            return PermissionDenied()

        if root.used_by_id is None:
            return _resolve_code(None)

        return (
            UserByUserIdLoader(info.context).load(root.used_by_id).then(_resolve_code)
        )

    @staticmethod
    def resolve_created_by(root: models.GiftCard, info):
        def _resolve_created_by(user):
            requestor = get_user_or_app_from_context(info.context)
            if requestor_has_access(requestor, user, AccountPermissions.MANAGE_USERS):
                return user

            return PermissionDenied()

        if root.created_by_id is None:
            return _resolve_created_by(None)

        return UserByUserIdLoader(info.context).load(root.created_by_id)

    @staticmethod
    def resolve_used_by(root: models.GiftCard, info):
        def _resolve_used_by(user):
            requestor = get_user_or_app_from_context(info.context)
            if requestor_has_access(requestor, user, AccountPermissions.MANAGE_USERS):
                return user

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
    def resolve_app(root: models.GiftCard, info):
        def _resolve_app(app):
            requester = get_user_or_app_from_context(info.context)
            if requester == app or requester.has_perm(AppPermission.MANAGE_APPS):
                return app
            return PermissionDenied()

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
    @permission_required(GiftcardPermissions.MANAGE_GIFT_CARD)
    def resolve_events(root: models.GiftCard, info, **kwargs):
        def filter_events(events):
            event_filter = kwargs.get("filter", {})
            if event_type_value := event_filter.get("type"):
                events = filter_events_by_type(events, event_type_value)
            if orders_value := event_filter.get("orders"):
                events = filter_events_by_orders(events, orders_value)
            return events

        return (
            GiftCardEventsByGiftCardIdLoader(info.context)
            .load(root.id)
            .then(filter_events)
        )

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

            order_id = bought_event.parameters["order_id"]
            return OrderByIdLoader(info.context).load(order_id).then(with_order)

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
            if requestor_has_access(requestor, user, AccountPermissions.MANAGE_USERS):
                return user

        if not root.created_by_id:
            return _resolve_user(None)

        return (
            UserByUserIdLoader(info.context)
            .load(root.created_by_id)
            .then(_resolve_user)
        )

    @staticmethod
    def resolve_end_date(root: models.GiftCard, *_args, **_kwargs):
        return root.expiry_date

    @staticmethod
    def resolve_start_date(root: models.GiftCard, *_args, **_kwargs):
        return None
