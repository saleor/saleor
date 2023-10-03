import graphene

from .types import SiteSettingsType
from ...pharmacy import models
from django.contrib.sites.models import Site

from ...pharmacy_settings import MEDIA_URL


class SiteSettingsInput(graphene.InputObjectType):
    name = graphene.String(description="Site Settings Name", required=True)
    pharmacy_name = graphene.String(description="Site Settings Pharmacy Name",
                                    required=True)
    npi = graphene.String(description="Site Settings NPI", required=True)
    phone_number = graphene.String(description="Site Settings Phone Number",
                                   required=True)
    fax_number = graphene.String(description="Site Settings Fax Number", required=True)
    image = graphene.String(description="Site Settings Image", required=True)
    css = graphene.String(description="Site Settings CSS")


class SiteSettingsCreate(graphene.Mutation):
    class Meta:
        description = "Creates a new Site Settings."

    class Arguments:
        input = SiteSettingsInput(
            description="Fields required to create a Site Settings", required=True
        )

    site_settings = graphene.Field(SiteSettingsType)

    @staticmethod
    def mutate(self, info, input: SiteSettingsInput):
        site_settings = models.SiteSettings(
            name=input.name,
            pharmacy_name=input.pharmacy_name,
            npi=input.npi,
            phone_number=input.phone_number,
            fax_number=input.fax_number,
        )

        site_settings.save()

        slug = str(input.name).lower().replace(" ", "-")
        existing_site_settings = models.SiteSettings.objects.filter(slug=slug).first()
        if existing_site_settings:
            slug = f"{slug}-{str(site_settings.pk)}"

        if input.image or input.css:
            import base64

            from django.core.files.base import ContentFile

            if input.image:
                file_content = base64.b64decode(input.image)
                site_settings.image.save(slug + '.svg', ContentFile(file_content))

            if input.css:
                file_content = base64.b64decode(input.css)
                site_settings.css.save(slug + '.css', ContentFile(file_content))

        site_settings.slug = slug
        site_settings.save()

        domain = Site.objects.get_current().domain
        site_settings.image = f"{domain}{MEDIA_URL}{site_settings.image}"
        site_settings.css = f"{domain}{MEDIA_URL}{site_settings.css}" \
            if site_settings.css else ""

        return SiteSettingsCreate(site_settings=site_settings)


class SiteSettingsUpdate(graphene.Mutation):
    class Meta:
        description = "Update Site Settings by id."

    class Arguments:
        id = graphene.ID(description="ID of Site Settings",
                         required=True)
        input = SiteSettingsInput(
            description="Fields required to create a Site Settings", required=True
        )

    site_settings = graphene.Field(SiteSettingsType)

    @staticmethod
    def mutate(self, info, id, input: SiteSettingsInput):
        site_settings = models.SiteSettings.objects.get(pk=id)

        if site_settings is None:
            raise Exception("Site settings id doesn't exits")

        site_settings.name = input.name
        site_settings.pharmacy_name = input.pharmacy_name
        site_settings.npi = input.npi
        site_settings.phone_number = input.phone_number
        site_settings.fax_number = input.fax_number

        site_settings.save()

        slug = str(input.name).lower().replace(" ", "-")
        existing_site_settings = models.SiteSettings.objects.filter(slug=slug).first()
        if existing_site_settings:
            slug = f"{slug}-{str(site_settings.pk)}"

        if input.image or input.css:
            import base64

            from django.core.files.base import ContentFile

            if input.image:
                file_content = base64.b64decode(input.image)
                site_settings.image.save(slug + '.svg', ContentFile(file_content))

            if input.css:
                file_content = base64.b64decode(input.css)
                site_settings.css.save(slug + '.css', ContentFile(file_content))

        site_settings.slug = slug
        site_settings.save()

        domain = Site.objects.get_current().domain
        site_settings.image = f"{domain}{MEDIA_URL}{site_settings.image}"
        site_settings.css = f"{domain}{MEDIA_URL}{site_settings.css}" \
            if site_settings.css else ""

        return SiteSettingsCreate(site_settings=site_settings)
