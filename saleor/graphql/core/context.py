import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from django.conf import settings
from django.http import HttpRequest
from django.utils.functional import empty

from ...account.models import User
from ...app.models import App

if TYPE_CHECKING:
    from .dataloaders import DataLoader


class SaleorContext(HttpRequest):
    _cached_user: Optional[User]
    decoded_auth_token: Optional[Dict[str, Any]]
    is_mutation: bool
    dataloaders: Dict[str, "DataLoader"]
    app: Optional[App]
    user: Optional[User]  # type: ignore[assignment]
    requestor: Union[App, User, None]
    request_time: datetime.datetime


def set_mutation_flag_in_context(context: SaleorContext) -> None:
    """Set information in context to don't use database replicas.

    Part of the database read replicas in Saleor.
    When Saleor builds a response for mutation `context` stores information
    `is_mutation=True`. That means that all data should be provided from
    the master database.
    When Saleor build a response for query `context` doesn't have the
    `is_mutation` field.
    That means that all data should be provided from reading replica of the database.
    Database read replica couldn't be used to save any data.
    """
    context.is_mutation = True


def get_database_connection_name(context: SaleorContext) -> str:
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


def setup_context_user(context: SaleorContext) -> None:
    if hasattr(context.user, "_wrapped") and (
        context.user._wrapped is empty or context.user._wrapped is None  # type: ignore
    ):
        context.user._setup()  # type: ignore
        context.user = context.user._wrapped  # type: ignore
