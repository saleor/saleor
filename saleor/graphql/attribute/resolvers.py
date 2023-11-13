from django.conf import settings

from ...attribute import models
from ..utils import get_user_or_app_from_context


def resolve_attributes(info, qs=None):
    requestor = get_user_or_app_from_context(info.context)
    qs = qs or models.Attribute.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).get_visible_to_user(requestor)
    return qs
