import graphene
import graphene_django_optimizer as gql_optimizer
from django.contrib.auth import get_user_model
from graphene import relay
from graphql_jwt.decorators import login_required, permission_required

from ...account import models
from ...checkout.utils import get_user_checkout
from ...core.permissions import get_permissions
from ...order import models as order_models
from ..checkout.types import Checkout
from ..core.connection import CountableDjangoObjectType
from ..core.fields import PrefetchingConnectionField
from ..core.resolvers import resolve_meta, resolve_private_meta
from ..core.types import CountryDisplay, Image, MetadataObjectType, PermissionDisplay
from ..core.utils import get_node_optimized
from ..utils import format_permissions_for_display
from .enums import CustomerEventsEnum


class AddressInput(graphene.InputObjectType):
    first_name = graphene.String(description="Given name.")
    last_name = graphene.String(description="Family name.")
    company_name = graphene.String(description="Company or organization.")
    street_address_1 = graphene.String(description="Address.")
    street_address_2 = graphene.String(description="Address.")
    city = graphene.String(description="City.")
    city_area = graphene.String(description="District.")
    postal_code = graphene.String(description="Postal code.")
    country = graphene.String(description="Country.")
    country_area = graphene.String(description="State or province.")
    phone = graphene.String(description="Phone number.")


class Address(CountableDjangoObjectType):
    country = graphene.Field(
        CountryDisplay, required=True, description="Default shop's country"
    )
    is_default_shipping_address = graphene.Boolean(
        required=False, description="Address is user's default shipping address"
    )
    is_default_billing_address = graphene.Boolean(
        required=False, description="Address is user's default billing address"
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
        """
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
        """
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


class CustomerEvent(CountableDjangoObjectType):
    date = graphene.types.datetime.DateTime(
        description="Date when event happened at in ISO 8601 format."
    )
    type = CustomerEventsEnum(description="Customer event type")
    user = graphene.Field(
        lambda: User,
        id=graphene.Argument(graphene.ID),
        description="User who performed the action.",
    )
    message = graphene.String(description="Content of the event.")
    count = graphene.Int(description="Number of objects concerned by the event.")
    order = gql_optimizer.field(
        graphene.Field(
            "saleor.graphql.order.types.Order", description="The concerned order."
        ),
        model_field="order",
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
                return get_node_optimized(qs, {"pk": order_line_pk}, info)
            except order_models.OrderLine.DoesNotExist:
                pass
        return None


class User(MetadataObjectType, CountableDjangoObjectType):
    addresses = gql_optimizer.field(
        graphene.List(Address, description="List of all user's addresses."),
        model_field="addresses",
    )
    checkout = graphene.Field(
        Checkout, description="Returns the last open checkout of this user."
    )
    gift_cards = gql_optimizer.field(
        PrefetchingConnectionField(
            "saleor.graphql.giftcard.types.GiftCard",
            description="List of the user gift cards.",
        ),
        model_field="gift_cards",
    )
    note = graphene.String(description="A note about the customer")
    orders = gql_optimizer.field(
        PrefetchingConnectionField(
            "saleor.graphql.order.types.Order", description="List of user's orders."
        ),
        model_field="orders",
    )
    permissions = graphene.List(
        PermissionDisplay, description="List of user's permissions."
    )
    avatar = graphene.Field(Image, size=graphene.Int(description="Size of the avatar."))
    events = gql_optimizer.field(
        graphene.List(
            CustomerEvent, description="List of events associated with the user."
        ),
        model_field="events",
    )
    stored_payment_sources = graphene.List(
        "saleor.graphql.payment.types.PaymentSource",
        description="List of stored payment sources",
    )

    class Meta:
        description = "Represents user data."
        interfaces = [relay.Node]
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
            "token",
        ]

    @staticmethod
    def resolve_addresses(root: models.User, _info, **_kwargs):
        return root.addresses.annotate_default(root).all()

    @staticmethod
    def resolve_checkout(root: models.User, _info, **_kwargs):
        return get_user_checkout(root)

    @staticmethod
    def resolve_gift_cards(root: models.User, info, **_kwargs):
        return root.gift_cards.all()

    @staticmethod
    def resolve_permissions(root: models.User, _info, **_kwargs):
        if root.is_superuser:
            permissions = get_permissions()
        else:
            permissions = root.user_permissions.prefetch_related(
                "content_type"
            ).order_by("codename")
        return format_permissions_for_display(permissions)

    @staticmethod
    @permission_required("account.manage_users")
    def resolve_note(root: models.User, _info):
        return root.note

    @staticmethod
    @permission_required("account.manage_users")
    def resolve_events(root: models.User, _info):
        return root.events.all()

    @staticmethod
    def resolve_orders(root: models.User, info, **_kwargs):
        viewer = info.context.user
        if viewer.has_perm("order.manage_orders"):
            return root.orders.all()
        return root.orders.confirmed()

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
    @login_required
    def resolve_stored_payment_sources(root: models.User, _info):
        from .resolvers import resolve_payment_sources

        return resolve_payment_sources(root)

    @staticmethod
    @permission_required("account.manage_users")
    def resolve_private_meta(root, _info):
        return resolve_private_meta(root, _info)

    @staticmethod
    def resolve_meta(root, _info):
        return resolve_meta(root, _info)


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
