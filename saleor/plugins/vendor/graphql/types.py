import graphene
from graphene import relay

from ....graphql.account.enums import CountryCodeEnum
from ....graphql.core.connection import CountableDjangoObjectType
from ....graphql.core.types.common import Image
from .. import models


class Vendor(CountableDjangoObjectType):
    users = graphene.List(graphene.ID, description="List of user IDs.")
    variants = graphene.List(graphene.ID, description="List of variant IDs.")
    logo = graphene.Field(Image, size=graphene.Int(description="Size of the image."))
    header_image = graphene.Field(
        Image, size=graphene.Int(description="Size of the image.")
    )
    description = graphene.JSONString(description="Editorjs formatted description")
    country = CountryCodeEnum(description="Country.")

    class Meta:
        model = models.Vendor
        filter_fields = ["id", "name", "country"]
        interfaces = (graphene.relay.Node,)

    def resolve_users(root, info):
        return root.users.values_list("id")

    def resolve_variants(root, info):
        return root.variants.values_list("id")

    def resolve_logo(root, info, size=None):
        if root.logo:
            return Image.get_adjusted(
                image=root.background_image,
                alt=f"{root.name}'s logo",
                size=size,
                rendition_key_set="logo",
                info=info,
            )

    def resolve_header_image(root, info, size=None):
        if root.header_image:
            return Image.get_adjusted(
                image=root.header_image,
                alt=f"{root.name}'s header image",
                size=size,
                rendition_key_set="background_images",
                info=info,
            )


class VendorConnection(relay.Connection):
    class Meta:
        node = Vendor


class Billing(CountableDjangoObjectType):
    class Meta:
        model = models.BillingInfo
        filter_fields = ["id", "iban", "bank_name"]
        interfaces = (graphene.relay.Node,)


class BillingConnection(relay.Connection):
    class Meta:
        node = Billing
