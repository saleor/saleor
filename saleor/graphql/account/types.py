import uuid
from typing import List

import graphene
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from graphene import relay

from ...account import models
from ...checkout.utils import get_user_checkout
from ...core.exceptions import PermissionDenied
from ...core.permissions import (
    AccountPermissions,
    AppPermission,
    AuthorizationFilters,
    OrderPermissions,
)
from ...core.tracing import traced_resolver
from ...order import OrderStatus
from ...thumbnail.utils import get_image_or_proxy_url, get_thumbnail_size
from ..account.utils import check_is_owner_or_has_one_of_perms
from ..app.dataloaders import AppByIdLoader
from ..app.types import App
from ..checkout.dataloaders import CheckoutByUserAndChannelLoader, CheckoutByUserLoader
from ..checkout.types import Checkout, CheckoutCountableConnection
from ..core.connection import CountableConnection, create_connection_slice
from ..core.descriptions import ADDED_IN_38, DEPRECATED_IN_3X_FIELD
from ..core.enums import LanguageCodeEnum
from ..core.federation import federated_entity, resolve_federation_references
from ..core.fields import ConnectionField, PermissionsField
from ..core.scalars import UUID
from ..core.types import (
    CountryDisplay,
    Image,
    ModelObjectType,
    NonNullList,
    Permission,
    ThumbnailField,
)
from ..core.utils import from_global_id_or_error, str_to_enum, to_global_id_or_none
from ..giftcard.dataloaders import GiftCardsByUserLoader
from ..meta.types import ObjectWithMetadata
from ..order.dataloaders import OrderLineByIdLoader, OrdersByUserLoader
from ..utils import format_permissions_for_display, get_user_or_app_from_context
from .dataloaders import (
    CustomerEventsByUserLoader,
    ThumbnailByUserIdSizeAndFormatLoader,
)
from .enums import CountryCodeEnum, CustomerEventsEnum
from .utils import can_user_manage_group, get_groups_which_user_can_manage


class AddressInput(graphene.InputObjectType):
    first_name = graphene.String(description="Given name.")
    last_name = graphene.String(description="Family name.")
    company_name = graphene.String(description="Company or organization.")
    street_address_1 = graphene.String(description="Address.")
    street_address_2 = graphene.String(description="Address.")
    city = graphene.String(description="City.")
    city_area = graphene.String(description="District.")
    postal_code = graphene.String(description="Postal code.")
    country = CountryCodeEnum(description="Country.")
    country_area = graphene.String(description="State or province.")
    phone = graphene.String(description="Phone number.")


@federated_entity("id")
class Address(ModelObjectType):
    id = graphene.GlobalID(required=True)
    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)
    company_name = graphene.String(required=True)
    street_address_1 = graphene.String(required=True)
    street_address_2 = graphene.String(required=True)
    city = graphene.String(required=True)
    city_area = graphene.String(required=True)
    postal_code = graphene.String(required=True)
    country = graphene.Field(
        CountryDisplay, required=True, description="Shop's default country."
    )
    country_area = graphene.String(required=True)
    phone = graphene.String()
    is_default_shipping_address = graphene.Boolean(
        required=False, description="Address is user's default shipping address."
    )
    is_default_billing_address = graphene.Boolean(
        required=False, description="Address is user's default billing address."
    )

    class Meta:
        description = "Represents user address data."
        interfaces = [relay.Node]
        model = models.Address

    @staticmethod
    def resolve_country(root: models.Address, _info):
        return CountryDisplay(code=root.country.code, country=root.country.name)

    @staticmethod
    def resolve_is_default_shipping_address(root: models.Address, _info):
        """Look if the address is the default shipping address of the user.

        This field is added through annotation when using the
        `resolve_addresses` resolver. It's invalid for
        `resolve_default_shipping_address` and
        `resolve_default_billing_address`
        """
        if not hasattr(root, "user_default_shipping_address_pk"):
            return None

        user_default_shipping_address_pk = getattr(
            root, "user_default_shipping_address_pk"
        )
        if user_default_shipping_address_pk == root.pk:
            return True
        return False

    @staticmethod
    def resolve_is_default_billing_address(root: models.Address, _info):
        """Look if the address is the default billing address of the user.

        This field is added through annotation when using the
        `resolve_addresses` resolver. It's invalid for
        `resolve_default_shipping_address` and
        `resolve_default_billing_address`
        """
        if not hasattr(root, "user_default_billing_address_pk"):
            return None

        user_default_billing_address_pk = getattr(
            root, "user_default_billing_address_pk"
        )
        if user_default_billing_address_pk == root.pk:
            return True
        return False

    @staticmethod
    def __resolve_references(roots: List["Address"], info):
        from .resolvers import resolve_addresses

        root_ids = [root.id for root in roots]
        addresses = {
            address.id: address for address in resolve_addresses(info, root_ids)
        }

        result = []
        for root_id in root_ids:
            _, root_id = from_global_id_or_error(root_id, Address)
            result.append(addresses.get(int(root_id)))
        return result


class CustomerEvent(ModelObjectType):
    id = graphene.GlobalID(required=True)
    date = graphene.types.datetime.DateTime(
        description="Date when event happened at in ISO 8601 format."
    )
    type = CustomerEventsEnum(description="Customer event type.")
    user = graphene.Field(lambda: User, description="User who performed the action.")
    app = graphene.Field(App, description="App that performed the action.")
    message = graphene.String(description="Content of the event.")
    count = graphene.Int(description="Number of objects concerned by the event.")
    order = graphene.Field(
        "saleor.graphql.order.types.Order", description="The concerned order."
    )
    order_line = graphene.Field(
        "saleor.graphql.order.types.OrderLine", description="The concerned order line."
    )

    class Meta:
        description = "History log of the customer."
        interfaces = [relay.Node]
        model = models.CustomerEvent

    @staticmethod
    def resolve_user(root: models.CustomerEvent, info):
        user = info.context.user
        if (
            user == root.user
            or user.has_perm(AccountPermissions.MANAGE_USERS)
            or user.has_perm(AccountPermissions.MANAGE_STAFF)
        ):
            return root.user
        raise PermissionDenied(
            permissions=[
                AccountPermissions.MANAGE_STAFF,
                AccountPermissions.MANAGE_USERS,
                AuthorizationFilters.OWNER,
            ]
        )

    @staticmethod
    def resolve_app(root: models.CustomerEvent, info):
        requestor = get_user_or_app_from_context(info.context)
        check_is_owner_or_has_one_of_perms(
            requestor, root.user, AppPermission.MANAGE_APPS
        )
        return AppByIdLoader(info.context).load(root.app_id) if root.app_id else None

    @staticmethod
    def resolve_message(root: models.CustomerEvent, _info):
        return root.parameters.get("message", None)

    @staticmethod
    def resolve_count(root: models.CustomerEvent, _info):
        return root.parameters.get("count", None)

    @staticmethod
    def resolve_order_line(root: models.CustomerEvent, info):
        if "order_line_pk" in root.parameters:
            return OrderLineByIdLoader(info.context).load(
                uuid.UUID(root.parameters["order_line_pk"])
            )
        return None


class UserPermission(Permission):
    source_permission_groups = NonNullList(
        "saleor.graphql.account.types.Group",
        description="List of user permission groups which contains this permission.",
        user_id=graphene.Argument(
            graphene.ID,
            description="ID of user whose groups should be returned.",
            required=True,
        ),
        required=False,
    )

    @staticmethod
    @traced_resolver
    def resolve_source_permission_groups(root: Permission, _info, user_id):
        _type, user_id = from_global_id_or_error(user_id, only_type="User")
        groups = auth_models.Group.objects.filter(
            user__pk=user_id, permissions__name=root.name
        )
        return groups


@federated_entity("id")
@federated_entity("email")
class User(ModelObjectType):
    id = graphene.GlobalID(required=True)
    email = graphene.String(required=True)
    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)
    is_staff = graphene.Boolean(required=True)
    is_active = graphene.Boolean(required=True)
    addresses = NonNullList(
        Address, description="List of all user's addresses.", required=True
    )
    checkout = graphene.Field(
        Checkout,
        description="Returns the last open checkout of this user.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} "
            "Use the `checkoutTokens` field to fetch the user checkouts."
        ),
    )
    checkout_tokens = NonNullList(
        UUID,
        description="Returns the checkout UUID's assigned to this user.",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        deprecation_reason=(f"{DEPRECATED_IN_3X_FIELD} Use `checkoutIds` instead."),
    )
    checkout_ids = NonNullList(
        graphene.ID,
        description="Returns the checkout ID's assigned to this user.",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
    )
    checkouts = ConnectionField(
        CheckoutCountableConnection,
        description="Returns checkouts assigned to this user." + ADDED_IN_38,
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
    )
    gift_cards = ConnectionField(
        "saleor.graphql.giftcard.types.GiftCardCountableConnection",
        description="List of the user gift cards.",
    )
    note = PermissionsField(
        graphene.String,
        description="A note about the customer.",
        permissions=[AccountPermissions.MANAGE_USERS, AccountPermissions.MANAGE_STAFF],
    )
    orders = ConnectionField(
        "saleor.graphql.order.types.OrderCountableConnection",
        description=(
            "List of user's orders. Requires one of the following permissions: "
            f"{AccountPermissions.MANAGE_STAFF.name}, "
            f"{AuthorizationFilters.OWNER.name}."
        ),
    )
    user_permissions = NonNullList(
        UserPermission, description="List of user's permissions."
    )
    permission_groups = NonNullList(
        "saleor.graphql.account.types.Group",
        description="List of user's permission groups.",
    )
    editable_groups = NonNullList(
        "saleor.graphql.account.types.Group",
        description="List of user's permission groups which user can manage.",
    )
    avatar = ThumbnailField()
    events = PermissionsField(
        NonNullList(CustomerEvent),
        description="List of events associated with the user.",
        permissions=[AccountPermissions.MANAGE_USERS, AccountPermissions.MANAGE_STAFF],
    )
    stored_payment_sources = NonNullList(
        "saleor.graphql.payment.types.PaymentSource",
        description="List of stored payment sources.",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
    )
    language_code = graphene.Field(
        LanguageCodeEnum, description="User language code.", required=True
    )
    default_shipping_address = graphene.Field(Address)
    default_billing_address = graphene.Field(Address)

    last_login = graphene.DateTime()
    date_joined = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)

    class Meta:
        description = "Represents user data."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = get_user_model()

    @staticmethod
    def resolve_addresses(root: models.User, _info):
        return root.addresses.annotate_default(root).all()  # type: ignore

    @staticmethod
    def resolve_checkout(root: models.User, _info):
        return get_user_checkout(root)

    @staticmethod
    @traced_resolver
    def resolve_checkout_tokens(root: models.User, info, channel=None):
        def return_checkout_tokens(checkouts):
            if not checkouts:
                return []
            checkout_global_ids = []
            for checkout in checkouts:
                checkout_global_ids.append(checkout.token)
            return checkout_global_ids

        if not channel:
            return (
                CheckoutByUserLoader(info.context)
                .load(root.id)
                .then(return_checkout_tokens)
            )
        return (
            CheckoutByUserAndChannelLoader(info.context)
            .load((root.id, channel))
            .then(return_checkout_tokens)
        )

    @staticmethod
    @traced_resolver
    def resolve_checkout_ids(root: models.User, info, channel=None):
        def return_checkout_ids(checkouts):
            if not checkouts:
                return []
            checkout_global_ids = []
            for checkout in checkouts:
                checkout_global_ids.append(to_global_id_or_none(checkout))
            return checkout_global_ids

        if not channel:
            return (
                CheckoutByUserLoader(info.context)
                .load(root.id)
                .then(return_checkout_ids)
            )
        return (
            CheckoutByUserAndChannelLoader(info.context)
            .load((root.id, channel))
            .then(return_checkout_ids)
        )

    @staticmethod
    def resolve_checkouts(root: models.User, info, **kwargs):
        def _resolve_checkouts(checkouts):
            return create_connection_slice(
                checkouts, info, kwargs, CheckoutCountableConnection
            )

        if channel := kwargs.get("channel"):
            return (
                CheckoutByUserAndChannelLoader(info.context)
                .load((root.id, channel))
                .then(_resolve_checkouts)
            )
        return CheckoutByUserLoader(info.context).load(root.id).then(_resolve_checkouts)

    @staticmethod
    def resolve_gift_cards(root: models.User, info, **kwargs):
        from ..giftcard.types import GiftCardCountableConnection

        def _resolve_gift_cards(gift_cards):
            return create_connection_slice(
                gift_cards, info, kwargs, GiftCardCountableConnection
            )

        return (
            GiftCardsByUserLoader(info.context).load(root.id).then(_resolve_gift_cards)
        )

    @staticmethod
    def resolve_user_permissions(root: models.User, _info):
        from .resolvers import resolve_permissions

        return resolve_permissions(root)

    @staticmethod
    def resolve_permission_groups(root: models.User, _info):
        return root.groups.all()

    @staticmethod
    def resolve_editable_groups(root: models.User, _info):
        return get_groups_which_user_can_manage(root)

    @staticmethod
    def resolve_note(root: models.User, info):
        return root.note

    @staticmethod
    def resolve_events(root: models.User, info):
        return CustomerEventsByUserLoader(info.context).load(root.id)

    @staticmethod
    def resolve_orders(root: models.User, info, **kwargs):
        from ..order.types import OrderCountableConnection

        def _resolve_orders(orders):
            requester = get_user_or_app_from_context(info.context)
            if not requester.has_perm(OrderPermissions.MANAGE_ORDERS):
                # allow fetch requestor orders (except drafts)
                if root == info.context.user:
                    orders = [
                        order for order in orders if order.status != OrderStatus.DRAFT
                    ]
                else:
                    raise PermissionDenied(
                        permissions=[
                            AuthorizationFilters.OWNER,
                            OrderPermissions.MANAGE_ORDERS,
                        ]
                    )

            return create_connection_slice(
                orders, info, kwargs, OrderCountableConnection
            )

        return OrdersByUserLoader(info.context).load(root.id).then(_resolve_orders)

    @staticmethod
    def resolve_avatar(root: models.User, info, size=None, format=None):
        if not root.avatar:
            return

        if not size:
            return Image(url=root.avatar.url, alt=None)

        format = format.lower() if format else None
        size = get_thumbnail_size(size)

        def _resolve_avatar(thumbnail):
            url = get_image_or_proxy_url(thumbnail, root.uuid, "User", size, format)
            return Image(url=url, alt=None)

        return (
            ThumbnailByUserIdSizeAndFormatLoader(info.context)
            .load((root.id, size, format))
            .then(_resolve_avatar)
        )

    @staticmethod
    def resolve_stored_payment_sources(root: models.User, info, channel=None):
        from .resolvers import resolve_payment_sources

        if root == info.context.user:
            return resolve_payment_sources(info, root, channel_slug=channel)
        raise PermissionDenied(permissions=[AuthorizationFilters.OWNER])

    @staticmethod
    def resolve_language_code(root, _info):
        return LanguageCodeEnum[str_to_enum(root.language_code)]

    @staticmethod
    def __resolve_references(roots: List["User"], info):
        from .resolvers import resolve_users

        ids = set()
        emails = set()
        for root in roots:
            if root.id is not None:
                ids.add(root.id)
            else:
                emails.add(root.email)

        users = list(resolve_users(info, ids=ids, emails=emails))
        users_by_id = {user.id: user for user in users}
        users_by_email = {user.email: user for user in users}

        results = []
        for root in roots:
            if root.id is not None:
                _, user_id = from_global_id_or_error(root.id, User)
                results.append(users_by_id.get(int(user_id)))
            else:
                results.append(users_by_email.get(root.email))
        return results


class UserCountableConnection(CountableConnection):
    class Meta:
        node = User


class ChoiceValue(graphene.ObjectType):
    raw = graphene.String()
    verbose = graphene.String()


class AddressValidationData(graphene.ObjectType):
    country_code = graphene.String(required=True)
    country_name = graphene.String(required=True)
    address_format = graphene.String(required=True)
    address_latin_format = graphene.String(required=True)
    allowed_fields = NonNullList(graphene.String, required=True)
    required_fields = NonNullList(graphene.String, required=True)
    upper_fields = NonNullList(graphene.String, required=True)
    country_area_type = graphene.String(required=True)
    country_area_choices = NonNullList(ChoiceValue, required=True)
    city_type = graphene.String(required=True)
    city_choices = NonNullList(ChoiceValue, required=True)
    city_area_type = graphene.String(required=True)
    city_area_choices = NonNullList(ChoiceValue, required=True)
    postal_code_type = graphene.String(required=True)
    postal_code_matchers = NonNullList(graphene.String, required=True)
    postal_code_examples = NonNullList(graphene.String, required=True)
    postal_code_prefix = graphene.String(required=True)


class StaffNotificationRecipient(graphene.ObjectType):
    id = graphene.ID(required=True)
    user = graphene.Field(
        User,
        description="Returns a user subscribed to email notifications.",
        required=False,
    )
    email = graphene.String(
        description=(
            "Returns email address of a user subscribed to email notifications."
        ),
        required=False,
    )
    active = graphene.Boolean(description="Determines if a notification active.")

    class Meta:
        description = (
            "Represents a recipient of email notifications send by Saleor, "
            "such as notifications about new orders. Notifications can be "
            "assigned to staff users or arbitrary email addresses."
        )
        interfaces = [relay.Node]
        model = models.StaffNotificationRecipient

    @staticmethod
    def get_node(info, id):
        try:
            return models.StaffNotificationRecipient.objects.get(pk=id)
        except models.StaffNotificationRecipient.DoesNotExist:
            return None

    @staticmethod
    def resolve_user(root: models.StaffNotificationRecipient, info):
        user = info.context.user
        if user == root.user or user.has_perm(AccountPermissions.MANAGE_STAFF):
            return root.user
        raise PermissionDenied(
            permissions=[AccountPermissions.MANAGE_STAFF, AuthorizationFilters.OWNER]
        )

    @staticmethod
    def resolve_email(root: models.StaffNotificationRecipient, _info):
        return root.get_email()


@federated_entity("id")
class Group(ModelObjectType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    users = PermissionsField(
        NonNullList(User),
        description="List of group users",
        permissions=[
            AccountPermissions.MANAGE_STAFF,
        ],
    )
    permissions = NonNullList(Permission, description="List of group permissions")
    user_can_manage = graphene.Boolean(
        required=True,
        description=(
            "True, if the currently authenticated user has rights to manage a group."
        ),
    )

    class Meta:
        description = "Represents permission group data."
        interfaces = [relay.Node]
        model = auth_models.Group

    @staticmethod
    def resolve_users(root: auth_models.Group, _info):
        return root.user_set.all()

    @staticmethod
    def resolve_permissions(root: auth_models.Group, _info):
        permissions = root.permissions.prefetch_related("content_type").order_by(
            "codename"
        )
        return format_permissions_for_display(permissions)

    @staticmethod
    def resolve_user_can_manage(root: auth_models.Group, info):
        user = info.context.user
        return can_user_manage_group(user, root)

    @staticmethod
    def __resolve_references(roots: List["Group"], info):
        from .resolvers import resolve_permission_groups

        requestor = get_user_or_app_from_context(info.context)
        if not requestor or not requestor.has_perm(AccountPermissions.MANAGE_STAFF):
            qs = auth_models.Group.objects.none()
        else:
            qs = resolve_permission_groups(info)

        return resolve_federation_references(Group, roots, qs)


class GroupCountableConnection(CountableConnection):
    class Meta:
        node = Group
