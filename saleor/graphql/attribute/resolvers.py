from ...attribute import models
from ..core.context import get_database_connection_name
from ..utils import get_user_or_app_from_context


def resolve_attributes(info, qs=None):
    if qs is None:
        requestor = get_user_or_app_from_context(info.context)
        qs = models.Attribute.objects.using(
            get_database_connection_name(info.context)
        ).get_visible_to_user(requestor)
    return qs
