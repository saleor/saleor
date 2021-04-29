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

    @staticmethod
    def resolve_media(self, info, post=None, slug=None, channel=None, **_kwargs):
        return models.PostMedia.objects.filter(post_id=self.pk)

@key(fields="id")
class PostMedia(CountableDjangoObjectType):
    class Meta:
        description = "Represents a post media."
        fields = ["alt", "id", "image", "sort_order", "type"]
        interfaces = [graphene.relay.Node]
        model = models.PostMedia

    @staticmethod
    def __resolve_reference(root, _info, **_kwargs):
        return graphene.Node.get_node_from_global_id(_info, root.id)