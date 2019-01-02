import graphene
from graphql_jwt.decorators import permission_required

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
    track_inventory_by_default = graphene.Boolean(
        description='Enable inventory tracking')
    default_weight_unit = WeightUnitsEnum(description='Default weight unit')


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

    @classmethod
    @permission_required('site.manage_settings')
    def mutate(cls, root, info, input):
        errors = []
        instance = info.context.site.settings

        for field_name, desired_value in input.items():
            current_value = getattr(instance, field_name)
            if current_value != desired_value:
                setattr(instance, field_name, desired_value)
        cls.clean_instance(instance, errors)

        if errors:
            return ShopSettingsUpdate(errors=errors)
        instance.save()
        return ShopSettingsUpdate(shop=Shop(), errors=errors)


class ShopDomainUpdate(BaseMutation):
    shop = graphene.Field(Shop, description='Updated Shop')

    class Arguments:
        input = SiteDomainInput(description='Fields required to update site')

    class Meta:
        description = 'Updates site domain of the shop'

    @classmethod
    @permission_required('site.manage_settings')
    def mutate(cls, root, info, input):
        errors = []
        site = info.context.site
        domain = input.get('domain')
        name = input.get('name')
        if domain is not None:
            site.domain = domain
        if name is not None:
            site.name = name
        cls.clean_instance(site, errors)
        if errors:
            return ShopDomainUpdate(errors=errors)
        site.save()
        return ShopDomainUpdate(shop=Shop(), errors=errors)


class HomepageCollectionUpdate(BaseMutation):
    shop = graphene.Field(Shop, description='Updated Shop')

    class Arguments:
        collection = graphene.ID(
            description='Collection displayed on homepage')

    class Meta:
        description = 'Updates homepage collection of the shop'

    @classmethod
    @permission_required('site.manage_settings')
    def mutate(cls, root, info, collection=None):
        errors = []
        new_collection = None
        if collection:
            new_collection = cls.get_node_or_error(
                info, collection, errors, 'collection', Collection)
        if errors:
            return HomepageCollectionUpdate(errors=errors)
        site_settings = info.context.site.settings
        site_settings.homepage_collection = new_collection
        cls.clean_instance(site_settings, errors)
        if errors:
            return HomepageCollectionUpdate(errors=errors)
        site_settings.save(update_fields=['homepage_collection'])
        return HomepageCollectionUpdate(shop=Shop(), errors=errors)


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

    class Arguments:
        key_type = AuthorizationKeyType(
            required=True, description='Type of an authorization key to add.')
        input = AuthorizationKeyInput(
            required=True,
            description='Fields required to create an authorization key.')

    @classmethod
    @permission_required('site.manage_settings')
    def mutate(cls, root, info, key_type, input):
        errors = []
        if site_models.AuthorizationKey.objects.filter(name=key_type).exists():
            cls.add_error(
                errors, 'key_type', 'Authorization key already exists.')
            return AuthorizationKeyAdd(errors=errors)

        site_settings = info.context.site.settings
        instance = site_models.AuthorizationKey(
            name=key_type, site_settings=site_settings, **input)
        cls.clean_instance(instance, errors)
        if errors:
            return AuthorizationKeyAdd(errors=errors)

        instance.save()
        return AuthorizationKeyAdd(authorization_key=instance, shop=Shop())


class AuthorizationKeyDelete(BaseMutation):
    authorization_key = graphene.Field(
        AuthorizationKey, description='Auhtorization key that was deleted.')
    shop = graphene.Field(Shop, description='Updated Shop')

    class Arguments:
        key_type = AuthorizationKeyType(
            required=True, description='Type of a key to delete.')

    class Meta:
        description = 'Deletes an authorization key.'

    @classmethod
    @permission_required('site.manage_settings')
    def mutate(cls, root, info, key_type):
        errors = []
        try:
            site_settings = info.context.site.settings
            instance = site_models.AuthorizationKey.objects.get(
                name=key_type, site_settings=site_settings)
        except site_models.AuthorizationKey.DoesNotExist:
            cls.add_error(
                errors, 'key_type', 'Couldn\'t resolve authorization key')
            return AuthorizationKeyDelete(errors=errors)

        instance.delete()
        return AuthorizationKeyDelete(authorization_key=instance, shop=Shop())
