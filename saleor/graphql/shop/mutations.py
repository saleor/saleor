
import graphene
from graphql_jwt.decorators import permission_required

from ..core.mutations import BaseMutation
from ..core.types.common import WeightUnitsEnum
from ..menu.types import Menu
from ..product.types import Collection
from .types import Shop


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


class ShopNavigationInput(graphene.InputObjectType):
    main = graphene.ID(description='Main navigation bar.')
    secondary = graphene.ID(description='Secondary navigation bar.')


class ShopSettingsUpdate(BaseMutation):
    class Arguments:
        input = ShopSettingsInput(
            description='Fields required to update shop settings.',
            required=True)

    shop = graphene.Field(
        Shop, description='Updated Shop')

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
    class Arguments:
        domain = graphene.String(description='Domain name for shop')

    shop = graphene.Field(
        Shop, description='Updated Shop')

    @classmethod
    @permission_required('site.manage_settings')
    def mutate(cls, root, info, domain):
        errors = []
        site = info.context.site
        site.domain = domain
        cls.clean_instance(site, errors)
        if errors:
            return ShopDomainUpdate(errors=errors)
        site.save(update_fields=['domain'])
        return ShopDomainUpdate(shop=Shop(), errors=errors)


class HomepageCollectionUpdate(BaseMutation):
    class Arguments:
        collection = graphene.ID(description='Collection displayed on homepage')

    shop = graphene.Field(
        Shop, description='Updated Shop')

    @classmethod
    @permission_required('site.manage_settings')
    def mutate(cls, root, info, collection):
        errors = []
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


class ShopNavigationUpdate(BaseMutation):
    class Arguments:
        input = ShopNavigationInput(
            description='Fields required to update shop navigation')

    shop = graphene.Field(
        Shop, description='Updated Shop')

    @classmethod
    @permission_required('site.manage_settings')
    def mutate(cls, root, info, input):
        errors = []
        main_menu_id = input.get('main')
        secondary_menu_id = input.get('secondary')
        main_menu, secondary_menu = None, None

        if main_menu_id:
            main_menu = cls.get_node_or_error(
                info, main_menu_id, errors, 'main', Menu)

        if secondary_menu_id:
            secondary_menu = cls.get_node_or_error(
                info, secondary_menu_id, errors, 'secondary', Menu)

        if errors:
            return ShopNavigationUpdate(errors=errors)

        site_settings = info.context.site.settings
        if main_menu:
            site_settings.top_menu = main_menu
        if secondary_menu:
            site_settings.bottom_menu = secondary_menu
        cls.clean_instance(site_settings, errors)
        if errors:
            return ShopNavigationUpdate(errors=errors)
        site_settings.save()
        return ShopNavigationUpdate(shop=Shop(), errors=errors)
