from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from django.http import HttpRequest


def get_database_connection_name(context: "HttpRequest"):
    is_mutation = getattr(context, "is_mutation", False)
    if not is_mutation:
        return settings.DATABASE_CONNECTION_REPLICA_NAME
    return settings.DATABASE_CONNECTION_DEFAULT_NAME
