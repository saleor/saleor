import graphene

from graphene_federation import key
from ...post import models
from ..core.connection import CountableDjangoObjectType
from ..meta.types import ObjectWithMetadata
from ..core.types import Image
from ...product.templatetags.product_images import (
    get_product_image_thumbnail,
    get_thumbnail,
)


class Post(CountableDjangoObjectType):
    title = graphene.String(
        description="The post title.",
        required=True,
    )
    content = graphene.String(
        description="The post content.",
        required=True,
    )
    media = graphene.List(
        graphene.NonNull(lambda: PostMedia),
        description="List of media for the post.",
    )

    class Meta:
        description = (
            "a post for store"
        )
        only_fields = [
            "title",
            "content"
        ]
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.Post

@key(fields="id")
class PostMedia(CountableDjangoObjectType):
    url = graphene.String(
        required=True,
        description="The URL of the media.",
        size=graphene.Int(description="Size of the image."),
    )

    class Meta:
        description = "Represents a product media."
        fields = ["alt", "id", "type"]
        interfaces = [graphene.relay.Node]
        model = models.PostMedia

    @staticmethod
    def resolve_url(root: models.PostMedia, info, *, size=None):
        if root.external_url:
            return root.external_url

        if size:
            url = get_thumbnail(root.image, size, method="thumbnail")
        else:
            url = root.image.url
        return info.context.build_absolute_uri(url)

    @staticmethod
    def __resolve_reference(root, _info, **_kwargs):
        return graphene.Node.get_node_from_global_id(_info, root.id)