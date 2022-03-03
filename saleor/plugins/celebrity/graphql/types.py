import graphene
from graphene import relay
from ....graphql.core.connection import CountableDjangoObjectType
from .. import models
from ....graphql.core.types.common import Image
from ....graphql.account.enums import CountryCodeEnum


class Celebrity(CountableDjangoObjectType):
    logo = graphene.Field(Image, size=graphene.Int(description="Size of the image."))
    header_image = graphene.Field(
        Image, size=graphene.Int(description="Size of the image.")
    )
    country = CountryCodeEnum(description="Country.")

    class Meta:
        model = models.Celebrity
        filter_field = ["id", "first_name", "phone_number", "email"]
        interfaces = (graphene.relay.Node,)

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


class CelebrityConnection(relay.Connection):
    class Meta:
        node = Celebrity
