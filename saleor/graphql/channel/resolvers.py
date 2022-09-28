from typing import Optional

from ...channel import models
from ...core.permissions import is_app, is_staff_user
from ..account.dataloaders import load_user
from ..app.dataloaders import load_app
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
    app = load_app(info.context)
    user = load_user(info.context)
    if is_staff_user(user) or is_app(app):
        return channel

    return None


def resolve_channels():
    return models.Channel.objects.all()
