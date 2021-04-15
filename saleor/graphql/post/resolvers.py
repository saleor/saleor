import graphene

from ...post import models
from ..core.validators import validate_one_of_args_is_in_query
from .types import Post


def resolve_post(info, global_page_id=None, slug=None):
    validate_one_of_args_is_in_query("id", global_page_id, "slug", slug)
    user = info.context.user

    if slug is not None:
        post = models.Post.objects.visible_to_user(user).filter(slug=slug).first()
    else:
        _type, post_pk = graphene.Node.from_global_id(global_page_id)
        store = models.Post.objects.visible_to_user(user).filter(pk=post_pk).first()
    return post


def resolve_posts(info, **_kwargs):
    return models.Post.objects.all()
