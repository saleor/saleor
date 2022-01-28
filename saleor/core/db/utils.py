from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from django.http import HttpRequest


def set_mutation_flag_in_context(context: "HttpRequest"):
    """Set information in context to don't use database replicas.

    Part of the database read replicas in Saleor.
    When Saleor builds a response for mutation `context` stores information
    `is_mutation=True`. That means that all data should be provided from
    the master database.
    When Saleor build a response for query `context` doesn’t have the
    `is_mutation` field.
    That means that all data should be provided from reading replica of the database.
    Database read replica couldn't be used to save any data.
    """
    context.is_mutation = True  # type: ignore


def get_database_connection_name(context: "HttpRequest"):
    """Retrieve connection name based on request context.

    Part of the database read replicas in Saleor.
    Return proper connection name based on `context`.
    For more info check `set_mutation_flag_in_context`
    Add `.using(connection_name)` to use connection name in QuerySet.
    Queryset to main database: `User.objects.all()`.
    Queryset to read replica: `User.objects.using(connection_name).all()`.
    """
    is_mutation = getattr(context, "is_mutation", False)
    if not is_mutation:
        return settings.DATABASE_CONNECTION_REPLICA_NAME
    return settings.DATABASE_CONNECTION_DEFAULT_NAME
