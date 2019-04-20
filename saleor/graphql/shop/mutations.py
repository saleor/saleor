import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import call_command

from ...site import models as site_models
from ..core.enums import WeightUnitsEnum
from ..core.mutations import BaseMutation
from ..product.types import Collection
from .types import AuthorizationKey, AuthorizationKeyType, Shop


class ShopSettingsInput(graphene.InputObjectType):
    header_text = graphene.String(description='Header text')
    description = graphene.String(description='SEO description')
    include_taxes_in_prices = graphene.Boolean(
        description='Include taxes in prices')
    display_gross_prices = graphene.Boolean(
        description='Display prices with tax in store')
    charge_taxes_on_shipping = graphene.Boolean(
        description='Charge taxes on shipping')
    track_inventory_by_default = graphene.Boolean(
        description='Enable inventory tracking')
    default_weight_unit = WeightUnitsEnum(description='Default weight unit')
    automatic_fulfillment_digital_products = graphene.Boolean(
        description='Enable automatic fulfillment for all digital products')
    default_digital_max_downloads = graphene.Int(
        description='Default number of max downloads per digital content url')
    default_digital_url_valid_days = graphene.Int(
        description=(
            'Default number of days which digital content url will be valid'))


class SiteDomainInput(graphene.InputObjectType):
    domain = graphene.String(description='Domain name for shop')
    name = graphene.String(description='Shop site name')


class ShopSettingsUpdate(BaseMutation):
    shop = graphene.Field(Shop, description='Updated Shop')

    class Arguments:
        input = ShopSettingsInput(
            description='Fields required to update shop settings.',
            required=True)

    class Meta:
        description = 'Updates shop settings'
        permissions = ('site.manage_settings', )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        instance = info.context.site.settings
        data = data.get('input')
        for field_name, desired_value in data.items():
            current_value = getattr(instance, field_name)
            if current_value != desired_value:
                setattr(instance, field_name, desired_value)
        cls.clean_instance(instance)
        instance.save()
        return ShopSettingsUpdate(shop=Shop())


class ShopDomainUpdate(BaseMutation):
    shop = graphene.Field(Shop, description='Updated Shop')

    class Arguments:
        input = SiteDomainInput(description='Fields required to update site')

    class Meta:
        description = 'Updates site domain of the shop'
        permissions = ('site.manage_settings', )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        site = info.context.site
        data = data.get('input')
        domain = data.get('domain')
        name = data.get('name')
        if domain is not None:
            site.domain = domain
        if name is not None:
            site.name = name
        cls.clean_instance(site)
        site.save()
        return ShopDomainUpdate(shop=Shop())


class ShopFetchTaxRates(BaseMutation):
    shop = graphene.Field(Shop, description='Updated Shop')

    class Meta:
        description = 'Fetch tax rates'
        permissions = ('site.manage_settings', )

    @classmethod
    def perform_mutation(cls, _root, _info):
        if not settings.VATLAYER_ACCESS_KEY:
            raise ValidationError(
                'Could not fetch tax rates. Make sure you have supplied a '
                'valid API Access Key.')
        call_command('get_vat_rates')
        return ShopFetchTaxRates(shop=Shop())


class HomepageCollectionUpdate(BaseMutation):
    shop = graphene.Field(Shop, description='Updated Shop')

    class Arguments:
        collection = graphene.ID(
            description='Collection displayed on homepage')

    class Meta:
        description = 'Updates homepage collection of the shop'
        permissions = ('site.manage_settings', )

    @classmethod
    def perform_mutation(cls, _root, info, collection=None):
        new_collection = cls.get_node_or_error(
            info, collection, field='collection', only_type=Collection)
        site_settings = info.context.site.settings
        site_settings.homepage_collection = new_collection
        cls.clean_instance(site_settings)
        site_settings.save(update_fields=['homepage_collection'])
        return HomepageCollectionUpdate(shop=Shop())


class AuthorizationKeyInput(graphene.InputObjectType):
    key = graphene.String(
        required=True, description='Client authorization key (client ID).')
    password = graphene.String(
        required=True, description='Client secret.')


class AuthorizationKeyAdd(BaseMutation):
    authorization_key = graphene.Field(
        AuthorizationKey, description='Newly added authorization key.')
    shop = graphene.Field(Shop, description='Updated Shop')

    class Meta:
        description = 'Adds an authorization key.'
        permissions = ('site.manage_settings', )

    class Arguments:
        key_type = AuthorizationKeyType(
            required=True, description='Type of an authorization key to add.')
        input = AuthorizationKeyInput(
            required=True,
            description='Fields required to create an authorization key.')

    @classmethod
    def perform_mutation(cls, _root, info, key_type, **data):
        if site_models.AuthorizationKey.objects.filter(name=key_type).exists():
            raise ValidationError({
                'key_type': 'Authorization key already exists.'})

        site_settings = info.context.site.settings
        instance = site_models.AuthorizationKey(
            name=key_type, site_settings=site_settings, **data.get('input'))
        cls.clean_instance(instance)
        instance.save()
        return AuthorizationKeyAdd(authorization_key=instance, shop=Shop())


class AuthorizationKeyDelete(BaseMutation):
    authorization_key = graphene.Field(
        AuthorizationKey, description='Authorization key that was deleted.')
    shop = graphene.Field(Shop, description='Updated Shop')

    class Arguments:
        key_type = AuthorizationKeyType(
            required=True, description='Type of a key to delete.')

    class Meta:
        description = 'Deletes an authorization key.'
        permissions = ('site.manage_settings', )

    @classmethod
    def perform_mutation(cls, _root, info, key_type):
        try:
            site_settings = info.context.site.settings
            instance = site_models.AuthorizationKey.objects.get(
                name=key_type, site_settings=site_settings)
        except site_models.AuthorizationKey.DoesNotExist:
            raise ValidationError({
                'key_type': 'Couldn\'t resolve authorization key'})

        instance.delete()
        return AuthorizationKeyDelete(authorization_key=instance, shop=Shop())
