import graphene
from graphene import relay

from ....graphql.account.enums import CountryCodeEnum
from ....graphql.core.connection import CountableDjangoObjectType
from ....graphql.core.types.common import Image
from .. import models


class Celebrity(CountableDjangoObjectType):
    products = graphene.List(graphene.ID, description="List of products IDs.")
    logo = graphene.Field(Image, size=graphene.Int(description="Size of the image."))
    header_image = graphene.Field(
        Image, size=graphene.Int(description="Size of the image.")
    )
    country = CountryCodeEnum(description="Country.")

    class Meta:
        model = models.Celebrity
        filter_field = ["id", "first_name", "phone_number", "email"]
        interfaces = (graphene.relay.Node,)

    def resolve_products(root, info):
        return [
            graphene.Node.to_global_id("Product", id)
            for id in root.products.values_list("id")
        ]

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
