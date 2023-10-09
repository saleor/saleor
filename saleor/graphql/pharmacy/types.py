import graphene
from graphene import relay
from ...pharmacy import models


class SiteSettingsType(graphene.ObjectType):
    class Meta:
        description = "The customer extensions for a Patient object."
        interfaces = [relay.Node]
        model = models.SiteSettings

    id = graphene.ID(required=True)
    name = graphene.String(required=True)
    slug = graphene.String(required=True)
    pharmacy_name = graphene.String(required=True)
    npi = graphene.String(required=True)
    phone_number = graphene.String(required=True)
    fax_number = graphene.String(required=True)
    image = graphene.String(required=True)
    css = graphene.String()


class SiteSettingsList(graphene.ObjectType):
    edge = graphene.List(SiteSettingsType)
