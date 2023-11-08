import graphene

from .types import SiteSettingsType
from .utils import build_file_uri
from ..core.scalars import PositiveDecimal
from ...permission.enums import SitePermissions
from ...pharmacy import models


class SiteSettingsInput(graphene.InputObjectType):
    name = graphene.String(description="Site Settings Name", required=True)
    slug = graphene.String(description="Site Settings Slug")
    pharmacy_name = graphene.String(description="Site Settings Pharmacy Name",
                                    required=True)
    npi = graphene.String(description="Site Settings NPI", required=True)
    phone_number = graphene.String(description="Site Settings Phone Number",
                                   required=True)
    fax_number = graphene.String(description="Site Settings Fax Number", required=True)
    image = graphene.String(description="Site Settings Image")
    cookies_src = graphene.String(description="Site Settings Cookies SRC")
    css = graphene.String(description="Site Settings CSS")
    is_active = graphene.Boolean(description="Active Site Settings")
    fill_fee_regular = graphene.Float(
        description="Site Settings Fill Fee Regular"
    )
    fill_fee_cold_chain = graphene.Float(
        description="Site Settings Fill Fee Cold Chain"
    )
    margin_regular = graphene.Float(
        description="Site Settings Margin Regular"
    )
    margin_cold_chain = graphene.Float(
        description="Site Settings Margin Cold Chain"
    )


class SiteSettingsCreate(graphene.Mutation):
    class Meta:
        description = "Creates a new Site Settings."
        permissions = (SitePermissions.MANAGE_SETTINGS,)

    class Arguments:
        input = SiteSettingsInput(
            description="Fields required to create a Site Settings", required=True
        )

    site_settings = graphene.Field(SiteSettingsType)

    @staticmethod
    def mutate(self, info, input: SiteSettingsInput):
        if input.is_active:
            update_data = {
                'is_active': False}
            models.SiteSettings.objects.update(**update_data)

        site_settings = models.SiteSettings(
            name=input.name,
            pharmacy_name=input.pharmacy_name,
            npi=input.npi,
            phone_number=input.phone_number,
            fax_number=input.fax_number,
            cookies_src=input.cookies_src,
            is_active=input.is_active,
            fill_fee_regular=input.fill_fee_regular,
            fill_fee_cold_chain=input.fill_fee_cold_chain,
            margin_regular=input.margin_regular,
            margin_cold_chain=input.margin_cold_chain,
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

        site_settings.image = build_file_uri(str(site_settings.image))
        site_settings.css = build_file_uri(str(site_settings.css))

        return SiteSettingsCreate(site_settings=site_settings)


class SiteSettingsUpdate(graphene.Mutation):
    class Meta:
        description = "Update Site Settings by id."
        permissions = (SitePermissions.MANAGE_SETTINGS,)

    class Arguments:
        id = graphene.ID(description="ID of Site Settings",
                         required=True)
        input = SiteSettingsInput(
            description="Fields required to create a Site Settings", required=True
        )

    site_settings = graphene.Field(SiteSettingsType)

    @staticmethod
    def mutate(self, info, id, input: SiteSettingsInput):
        if input.is_active:
            update_data = {
                'is_active': False}
            models.SiteSettings.objects.update(**update_data)
        site_settings = models.SiteSettings.objects.get(pk=id)

        if site_settings is None:
            raise Exception("Site settings id doesn't exits")

        site_settings.name = input.name
        site_settings.pharmacy_name = input.pharmacy_name
        site_settings.npi = input.npi
        site_settings.phone_number = input.phone_number
        site_settings.fax_number = input.fax_number
        site_settings.cookies_src = input.cookies_src
        site_settings.is_active = input.is_active
        site_settings.fill_fee_regular = input.fill_fee_regular
        site_settings.fill_fee_cold_chain = input.fill_fee_cold_chain
        site_settings.margin_regular = input.margin_regular
        site_settings.margin_cold_chain = input.margin_cold_chain

        site_settings.save()

        slug = str(input.slug).lower().replace(" ", "-")
        existing_site_settings = models.SiteSettings.objects.filter(slug=slug).first()
        if site_settings.slug != input.slug and existing_site_settings:
            slug = f"{slug}-{str(site_settings.pk)}"

        import base64
        from django.core.files.base import ContentFile

        if input.image and str(site_settings.image) not in input.image:
            file_content = base64.b64decode(input.image)
            site_settings.image.save(slug + '.svg', ContentFile(file_content))

        if input.css and (not site_settings.css or str(site_settings.css) not in input.css):
            file_content = base64.b64decode(input.css)
            site_settings.css.save(slug + '.css', ContentFile(file_content))
        elif not input.css:
            site_settings.css = ''

        site_settings.slug = slug
        site_settings.save()

        site_settings.image = build_file_uri(str(site_settings.image))
        site_settings.css = build_file_uri(str(site_settings.css))

        return SiteSettingsUpdate(site_settings=site_settings)


class SiteSettingsDelete(graphene.Mutation):
    class Meta:
        description = "Delete Site Settings by slug."
        permissions = (SitePermissions.MANAGE_SETTINGS,)

    class Arguments:
        slug = graphene.String(description="Site Settings Slug")

    success = graphene.Boolean()

    @staticmethod
    def mutate(self, info, slug):
        site_settings = models.SiteSettings.objects.filter(slug=slug).first()

        if site_settings is None:
            raise Exception("Site settings slug doesn't exits")

        site_settings.delete()

        return SiteSettingsDelete(success=True)
