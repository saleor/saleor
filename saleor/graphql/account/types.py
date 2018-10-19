import graphene
import graphene_django_optimizer as gql_optimizer
from django.contrib.auth import get_user_model
from graphene import relay

from ...account import models
from ...core.permissions import get_permissions
from ..core.fields import PrefetchingConnectionField
from ..core.types.common import (
    CountableDjangoObjectType, CountryDisplay, PermissionDisplay)
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
    country = graphene.String(required=True, description='Country.')
    country_area = graphene.String(description='State or province.')
    phone = graphene.String(description='Phone number.')


class Address(CountableDjangoObjectType):
    country = graphene.Field(
        CountryDisplay, required=True, description='Default shop\'s country')

    class Meta:
        exclude_fields = ['user_set', 'user_addresses']
        description = 'Represents user address data.'
        interfaces = [relay.Node]
        model = models.Address

    def resolve_country(self, info):
        return CountryDisplay(
            code=self.country.code, country=self.country.name)


class User(CountableDjangoObjectType):
    permissions = graphene.List(
        PermissionDisplay, description='List of user\'s permissions.')
    addresses = gql_optimizer.field(
        PrefetchingConnectionField(
            Address, description='List of all user\'s addresses.'),
        model_field='addresses')

    class Meta:
        exclude_fields = ['password', 'is_superuser', 'OrderEvent_set']
        description = 'Represents user data.'
        interfaces = [relay.Node]
        model = get_user_model()

    def resolve_permissions(self, info, **kwargs):
        if self.is_superuser:
            permissions = get_permissions()
        else:
            permissions = self.user_permissions.prefetch_related(
                'content_type').order_by('codename')
        return format_permissions_for_display(permissions)

    def resolve_addresses(self, info, **kwargs):
        return self.addresses.all()


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
    city_area_choices = graphene.List(ChoiceValue)
    postal_code_type = graphene.String()
    postal_code_matchers = graphene.List(graphene.String)
    postal_code_examples = graphene.List(graphene.String)
    postal_code_prefix = graphene.String()
