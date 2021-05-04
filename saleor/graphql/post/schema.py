import graphene

from ...core.permissions import StorePermissions
from ..channel.types import ChannelContext
from ..core.fields import PrefetchingConnectionField
from ..decorators import permission_required

from .types import Post
from ..store.types import Store
from ..core.fields import FilterInputConnectionField
from ..core.types import FilterInputObjectType
from .filters import PostFilterInput
from .sorters import PostSortingInput
from .mutations.posts import (
    PostCreate,
    PostDelete,
    PostUpdate,
    PostMediaCreate,
    PostMediaUpdate,
    PostMediaReorder,
)
from .resolvers import (
    resolve_post,
    resolve_posts,
)

class PostQueries(graphene.ObjectType):
    post = graphene.Field(
        Post,
        id=graphene.Argument(
            graphene.ID,
            description="ID of the post.",
        ),
        description="Look up a post by ID.",
    )

    posts = FilterInputConnectionField(
        Post,
        filter=PostFilterInput(description="Filtering options for post."),
        sort_by=PostSortingInput(description="Sort post."),
        description="List of the post.",
    )

    store = graphene.Field(
        Store,
        id=graphene.Argument(graphene.ID, description="ID of the store type."),
        description="Look up a store type by ID or slug.",
    )

    def resolve_post(self, info, id=None, slug=None):
        return resolve_post(info, id, slug)

    def resolve_posts(self, info, **kwargs):
        return resolve_posts(info, **kwargs)



class PostMutations(graphene.ObjectType):
    # post mutations
    post_create = PostCreate.Field()
    post_delete = PostDelete.Field()
    post_update = PostUpdate.Field()

    # post media mutations
    post_media_create = PostMediaCreate.Field()
    post_media_update = PostMediaUpdate.Field()
    post_media_reorder = PostMediaReorder.Field()