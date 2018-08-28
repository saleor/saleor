
import graphene

from ...site import models
from ..core.mutations import BaseMutation
from ..core.types.common import WeightUnitsEnum
from .types import SiteSettings


class SiteSettingsInput(graphene.InputObjectType):
    domain = graphene.String(description='Domain name for shop')
    header_text = graphene.String(description='Header text')
    description = graphene.String(description='SEO description')
    top_menu = graphene.ID(
        description='Menu to use on site top')
    bottom_menu = graphene.ID(
        description='Menu to use on site bottom')
    include_taxes_in_prices = graphene.Boolean(
        description='Include taxes in prices')
    display_gross_prices = graphene.Boolean(
        description='Display prices with tax in store')
    track_inventory_by_default = graphene.Boolean(
        description='Enable inventory tracking')
    homepage_collection = graphene.ID(
        description='Collection displayed on homepage')
    default_weight_unit = WeightUnitsEnum(description='Default weight unit')


class SiteSettingsUpdate(BaseMutation):
    class Arguments:
        input = SiteSettingsInput(
            description='Fields required to update site settings.',
            required=True)

    site_settings = graphene.Field(
        SiteSettings, description='Current site settings')

    @classmethod
    def mutate(cls, root, info, input):
        errors = []
        instance = info.context.site.settings
        domain = input.pop('domain', None)
        if domain:
            instance.site.domain = domain
            instance.site.save(update_fields=['domain'])

        for field_name, desired_value in input.items():
            current_value = getattr(instance, field_name)
            if current_value != desired_value:
                setattr(instance, field_name, desired_value)

        cls.clean_instance(instance, errors)
        if errors:
            return SiteSettingsUpdate(errors=errors)
        return SiteSettingsUpdate(site_settings=instance, errors=errors)
