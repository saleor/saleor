import graphene
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from graphene import relay
from graphene_federation import key

from ...account import models
from ...checkout.utils import get_user_checkout
from ...core.exceptions import PermissionDenied
from ...core.permissions import AccountPermissions, OrderPermissions
from ...order import models as order_models
from ..checkout.dataloaders import CheckoutByUserAndChannelLoader, CheckoutByUserLoader
from ..checkout.types import Checkout
from ..core.connection import CountableDjangoObjectType
from ..core.fields import PrefetchingConnectionField
from ..core.scalars import UUID
from ..core.types import CountryDisplay, Image, Permission
from ..core.utils import from_global_id_strict_type
from ..decorators import one_of_permissions_required, permission_required
from ..meta.types import ObjectWithMetadata
from ..utils import format_permissions_for_display
from ..wishlist.resolvers import resolve_wishlist_items_from_user
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


@key(fields="id")
class Address(CountableDjangoObjectType):
    country = graphene.Field(
        CountryDisplay, required=True, description="Shop's default country."
    )
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
        only_fields = [
            "city",
            "city_area",
            "company_name",
            "country",
            "country_area",
            "first_name",
            "id",
            "last_name",
            "phone",
            "postal_code",
            "street_address_1",
            "street_address_2",
        ]

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
    def __resolve_reference(root, _info, **_kwargs):
        return graphene.Node.get_node_from_global_id(_info, root.id)


class CustomerEvent(CountableDjangoObjectType):
    date = graphene.types.datetime.DateTime(
        description="Date when event happened at in ISO 8601 format."
    )
    type = CustomerEventsEnum(description="Customer event type.")
    user = graphene.Field(lambda: User, description="User who performed the action.")
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
        model = models.CustomerEvent
        interfaces = [relay.Node]
        only_fields = ["id"]

    @staticmethod
    def resolve_user(root: models.CustomerEvent, info):
        user = info.context.user
        if (
            user == root.user
            or user.has_perm(AccountPermissions.MANAGE_USERS)
            or user.has_perm(AccountPermissions.MANAGE_STAFF)
        ):
            return root.user
        raise PermissionDenied()

    @staticmethod
    def resolve_message(root: models.CustomerEvent, _info):
        return root.parameters.get("message", None)

    @staticmethod
    def resolve_count(root: models.CustomerEvent, _info):
        return root.parameters.get("count", None)

    @staticmethod
    def resolve_order_line(root: models.CustomerEvent, info):
        if "order_line_pk" in root.parameters:
            try:
                qs = order_models.OrderLine.objects
                order_line_pk = root.parameters["order_line_pk"]
                return qs.filter(pk=order_line_pk).first()
            except order_models.OrderLine.DoesNotExist:
                pass
        return None


class UserPermission(Permission):
    source_permission_groups = graphene.List(
        graphene.NonNull("saleor.graphql.account.types.Group"),
        description="List of user permission groups which contains this permission.",
        user_id=graphene.Argument(
            graphene.ID,
            description="ID of user whose groups should be returned.",
            required=True,
        ),
        required=False,
    )

    def resolve_source_permission_groups(root: Permission, _info, user_id, **_kwargs):
        user_id = from_global_id_strict_type(user_id, only_type="User", field="pk")
        groups = auth_models.Group.objects.filter(
            user__pk=user_id, permissions__name=root.name
        )
        return groups


@key("id")
@key("email")
class User(CountableDjangoObjectType):
    addresses = graphene.List(Address, description="List of all user's addresses.")
    checkout = graphene.Field(
        Checkout,
        description="Returns the last open checkout of this user.",
        deprecation_reason=(
            "Use the `checkout_tokens` field to fetch the user checkouts."
        ),
    )
    checkout_tokens = graphene.List(
        graphene.NonNull(UUID),
        description="Returns the checkout UUID's assigned to this user.",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
    )
    gift_cards = PrefetchingConnectionField(
        "saleor.graphql.giftcard.types.GiftCard",
        description="List of the user gift cards.",
    )
    note = graphene.String(description="A note about the customer.")
    orders = PrefetchingConnectionField(
        "saleor.graphql.order.types.Order", description="List of user's orders."
    )
    # deprecated, to remove in #5389
    permissions = graphene.List(
        Permission,
        description="List of user's permissions.",
        deprecation_reason=(
            "Will be removed in Saleor 2.11." "Use the `userPermissions` instead."
        ),
    )
    user_permissions = graphene.List(
        UserPermission, description="List of user's permissions."
    )
    permission_groups = graphene.List(
        "saleor.graphql.account.types.Group",
        description="List of user's permission groups.",
    )
    editable_groups = graphene.List(
        "saleor.graphql.account.types.Group",
        description="List of user's permission groups which user can manage.",
    )
    avatar = graphene.Field(Image, size=graphene.Int(description="Size of the avatar."))
    events = graphene.List(
        CustomerEvent, description="List of events associated with the user."
    )
    stored_payment_sources = graphene.List(
        "saleor.graphql.payment.types.PaymentSource",
        description="List of stored payment sources.",
    )

    class Meta:
        description = "Represents user data."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = get_user_model()
        only_fields = [
            "date_joined",
            "default_billing_address",
            "default_shipping_address",
            "email",
            "first_name",
            "id",
            "is_active",
            "is_staff",
            "last_login",
            "last_name",
            "note",
        ]

    @staticmethod
    def resolve_addresses(root: models.User, _info, **_kwargs):
        return root.addresses.annotate_default(root).all()

    @staticmethod
    def resolve_checkout(root: models.User, _info, **_kwargs):
        return get_user_checkout(root)

    @staticmethod
    def resolve_checkout_tokens(root: models.User, info, channel=None, **_kwargs):
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
    def resolve_gift_cards(root: models.User, info, **_kwargs):
        return root.gift_cards.all()

    @staticmethod
    def resolve_permissions(root: models.User, _info, **_kwargs):
        # deprecated, to remove in #5389
        from .resolvers import resolve_permissions

        return resolve_permissions(root)

    @staticmethod
    def resolve_user_permissions(root: models.User, _info, **_kwargs):
        from .resolvers import resolve_permissions

        return resolve_permissions(root)

    @staticmethod
    def resolve_permission_groups(root: models.User, _info, **_kwargs):
        return root.groups.all()

    @staticmethod
    def resolve_editable_groups(root: models.User, _info, **_kwargs):
        return get_groups_which_user_can_manage(root)

    @staticmethod
    @one_of_permissions_required(
        [AccountPermissions.MANAGE_USERS, AccountPermissions.MANAGE_STAFF]
    )
    def resolve_note(root: models.User, info):
        return root.note

    @staticmethod
    @one_of_permissions_required(
        [AccountPermissions.MANAGE_USERS, AccountPermissions.MANAGE_STAFF]
    )
    def resolve_events(root: models.User, info):
        return root.events.all()

    @staticmethod
    def resolve_orders(root: models.User, info, **_kwargs):
        viewer = info.context.user
        if viewer.has_perm(OrderPermissions.MANAGE_ORDERS):
            return root.orders.all()  # type: ignore
        return root.orders.confirmed()  # type: ignore

    @staticmethod
    def resolve_avatar(root: models.User, info, size=None, **_kwargs):
        if root.avatar:
            return Image.get_adjusted(
                image=root.avatar,
                alt=None,
                size=size,
                rendition_key_set="user_avatars",
                info=info,
            )

    @staticmethod
    def resolve_stored_payment_sources(root: models.User, info):
        from .resolvers import resolve_payment_sources

        if root == info.context.user:
            return resolve_payment_sources(root)
        raise PermissionDenied()

    @staticmethod
    def resolve_wishlist(root: models.User, info, **_kwargs):
        return resolve_wishlist_items_from_user(root)

    @staticmethod
    def __resolve_reference(root, _info, **_kwargs):
        if root.id is not None:
            return graphene.Node.get_node_from_global_id(_info, root.id)
        return get_user_model().objects.get(email=root.email)


class ChoiceValue(graphene.ObjectType):
    raw = graphene.String()
    verbose = graphene.String()


class AddressValidationData(graphene.ObjectType):
    country_code = graphene.String()
    country_name = graphene.String()
    address_format = graphene.String()
    address_latin_format = graphene.String()
    allowed_fields = graphene.List(graphene.String)
    required_fields = graphene.List(graphene.String)
    upper_fields = graphene.List(graphene.String)
    country_area_type = graphene.String()
    country_area_choices = graphene.List(ChoiceValue)
    city_type = graphene.String()
    city_choices = graphene.List(ChoiceValue)
    city_area_type = graphene.String()
    city_area_choices = graphene.List(ChoiceValue)
    postal_code_type = graphene.String()
    postal_code_matchers = graphene.List(graphene.String)
    postal_code_examples = graphene.List(graphene.String)
    postal_code_prefix = graphene.String()


class StaffNotificationRecipient(CountableDjangoObjectType):
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
        only_fields = ["user", "active"]

    @staticmethod
    def resolve_user(root: models.StaffNotificationRecipient, info):
        user = info.context.user
        if user == root.user or user.has_perm(AccountPermissions.MANAGE_STAFF):
            return root.user
        raise PermissionDenied()

    @staticmethod
    def resolve_email(root: models.StaffNotificationRecipient, _info):
        return root.get_email()


@key(fields="id")
class Group(CountableDjangoObjectType):
    users = graphene.List(User, description="List of group users")
    permissions = graphene.List(Permission, description="List of group permissions")
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
        only_fields = ["name", "permissions", "id"]

    @staticmethod
    @permission_required(AccountPermissions.MANAGE_STAFF)
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
