from typing import Optional

from ...channel import models
from ...permission.auth_filters import is_app, is_staff_user
from ..core.utils import from_global_id_or_error
from ..core.validators import validate_one_of_args_is_in_query
from .types import Channel


def resolve_channel(info, id: Optional[str], slug: Optional[str]):
    validate_one_of_args_is_in_query("id", id, "slug", slug)
    if id:
        _, db_id = from_global_id_or_error(id, Channel)
        channel = models.Channel.objects.filter(id=db_id).first()
    else:
        channel = models.Channel.objects.filter(slug=slug).first()

    if channel and channel.is_active:
        return channel
    if is_staff_user(info.context) or is_app(info.context):
        return channel

    return None


def resolve_channels():
    return models.Channel.objects.all()
