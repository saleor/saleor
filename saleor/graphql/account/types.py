import graphene
import graphene_django_optimizer as gql_optimizer
from django.contrib.auth import get_user_model
from graphene import relay
from graphql_jwt.decorators import permission_required

from ...account import models
from ...checkout.utils import get_user_checkout
from ...core.permissions import get_permissions
from ..checkout.types import Checkout
from ..core.connection import CountableDjangoObjectType
from ..core.fields import PrefetchingConnectionField
from ..core.types import CountryDisplay, Image, PermissionDisplay
from ..utils import format_permissions_for_display


class AddressInput(graphene.InputObjectType):
    first_name = graphene.String(description='Given name.')
    last_name = graphene.String(description='Family name.')
    company_name = graphene.String(description='Company or organization.')
    street_address_1 = graphene.String(description='Address.')
    street_address_2 = graphene.String(description='Address.')
    city = graphene.String(description='City.')
    city_area = graphene.String(description='District.')
    postal_code = graphene.String(description='Postal code.')
    country = graphene.String(description='Country.')
    country_area = graphene.String(description='State or province.')
    phone = graphene.String(description='Phone number.')


class Address(CountableDjangoObjectType):
    country = graphene.Field(
        CountryDisplay, required=True, description='Default shop\'s country')
    is_default_shipping_address = graphene.Boolean(
        required=False,
        description='Address is user\'s default shipping address')
    is_default_billing_address = graphene.Boolean(
        required=False,
        description='Address is user\'s default billing address')

    class Meta:
        description = 'Represents user address data.'
        interfaces = [relay.Node]
        model = models.Address
        only_fields = [
            'city', 'city_area', 'company_name', 'country', 'country_area',
            'first_name', 'id', 'last_name', 'phone', 'postal_code',
            'street_address_1', 'street_address_2']

    def resolve_country(self, _info):
        return CountryDisplay(
            code=self.country.code, country=self.country.name)

    def resolve_is_default_shipping_address(self, _info):
        """
        This field is added through annotation when using the
        `resolve_addresses` resolver. It's invalid for
        `resolve_default_shipping_address` and
        `resolve_default_billing_address`
        """
        if not hasattr(self, 'user_default_shipping_address_pk'):
            return None

        user_default_shipping_address_pk = getattr(
            self, 'user_default_shipping_address_pk')
        if user_default_shipping_address_pk == self.pk:
            return True
        return False

    def resolve_is_default_billing_address(self, _info):
        """
        This field is added through annotation when using the
        `resolve_addresses` resolver. It's invalid for
        `resolve_default_shipping_address` and
        `resolve_default_billing_address`
        """
        if not hasattr(self, 'user_default_billing_address_pk'):
            return None

        user_default_billing_address_pk = getattr(
            self, 'user_default_billing_address_pk')
        if user_default_billing_address_pk == self.pk:
            return True
        return False


class User(CountableDjangoObjectType):
    addresses = gql_optimizer.field(
        graphene.List(Address, description='List of all user\'s addresses.'),
        model_field='addresses')
    checkout = graphene.Field(
        Checkout,
        description='Returns the last open checkout of this user.')
    note = graphene.String(description='A note about the customer')
    orders = gql_optimizer.field(
        PrefetchingConnectionField(
            'saleor.graphql.order.types.Order',
            description='List of user\'s orders.'),
        model_field='orders')
    permissions = graphene.List(
        PermissionDisplay, description='List of user\'s permissions.')
    avatar = graphene.Field(
        Image, size=graphene.Int(description='Size of the avatar.'))

    class Meta:
        description = 'Represents user data.'
        interfaces = [relay.Node]
        model = get_user_model()
        only_fields = [
            'date_joined', 'default_billing_address',
            'default_shipping_address', 'email', 'first_name', 'id',
            'is_active', 'is_staff', 'last_login', 'last_name', 'note',
            'token']

    def resolve_addresses(self, _info, **_kwargs):
        return self.addresses.annotate_default(self).all()

    def resolve_checkout(self, _info, **_kwargs):
        return get_user_checkout(self)

    def resolve_permissions(self, _info, **_kwargs):
        if self.is_superuser:
            permissions = get_permissions()
        else:
            permissions = self.user_permissions.prefetch_related(
                'content_type').order_by('codename')
        return format_permissions_for_display(permissions)

    @permission_required('account.manage_users')
    def resolve_note(self, _info):
        return self.note

    def resolve_orders(self, info, **_kwargs):
        viewer = info.context.user
        if viewer.has_perm('order.manage_orders'):
            return self.orders.all()
        return self.orders.confirmed()

    def resolve_avatar(self, info, size=None, **_kwargs):
        if self.avatar:
            return Image.get_adjusted(
                image=self.avatar,
                alt=None,
                size=size,
                rendition_key_set='user_avatars',
                info=info,
            )


class AddressValidationInput(graphene.InputObjectType):
    country_code = graphene.String()
    country_area = graphene.String()
    city_area = graphene.String()


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
