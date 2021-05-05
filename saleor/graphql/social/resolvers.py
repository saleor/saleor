import graphene

from ...social import models
from ..core.validators import validate_one_of_args_is_in_query
from .types import Social


def resolve_social(info, global_page_id=None, slug=None):
    validate_one_of_args_is_in_query("id", global_page_id, "slug", slug)    

    if slug is not None:
        social = models.Social.objects.filter(slug=slug).first()
    else:
        _type, social_pk = graphene.Node.from_global_id(global_page_id)
        social = models.Social.objects.filter(pk=social_pk).all()
    return social


def resolve_socials(info, **_kwargs):
    user = info.context.user
    return models.Social.objects.all().filter(user=user).all()
