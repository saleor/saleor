import graphene

from ...social import models
from ..core.validators import validate_one_of_args_is_in_query
from .types import Social


def resolve_social(info, slug=None):
    user = info.context.user

    if slug is not None:
        social = models.Social.objects.filter(slug=slug).first()
    else:
        social = models.Social.objects.filter(user=user).first()
    return social


def resolve_socials(info, **_kwargs):
    return models.Social.objects.all()
