
import graphene
from ..core.mutations import ModelMutation
from ..core.types.common import WeightUnitsEnum

from ...site import models

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


class SiteSettingsUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(
            description='ID of a customer to update.', required=True)
        input = SiteSettingsInput(
            description='Fields required to update site settings.',
            required=True)

    class Meta:
        model = models.SiteSettings
        exclude = ['translated']

    @classmethod
    def save(cls, info, instance, cleaned_input):
        domain = cleaned_input.get('domain')
        if domain:
            instance.site.domain = domain
            instance.site.save()
        super().save(info, instance, cleaned_input)
