from ...channel import models
from ...permission.auth_filters import is_app, is_staff_user
from ..core.context import get_database_connection_name
from ..core.utils import from_global_id_or_error
from ..core.validators import validate_one_of_args_is_in_query
from .types import Channel


def resolve_channel(info, id: str | None, slug: str | None):
    validate_one_of_args_is_in_query("id", id, "slug", slug)
    if id:
        _, db_id = from_global_id_or_error(id, Channel)
        channel = (
            models.Channel.objects.using(get_database_connection_name(info.context))
            .filter(id=db_id)
            .first()
        )
    else:
        channel = (
            models.Channel.objects.using(get_database_connection_name(info.context))
            .filter(slug=slug)
            .first()
        )

    if channel and channel.is_active:
        return channel
    if is_staff_user(info.context) or is_app(info.context):
        return channel

    return None


def resolve_channels(info):
    return models.Channel.objects.using(
        get_database_connection_name(info.context)
    ).all()
