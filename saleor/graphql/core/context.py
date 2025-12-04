import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from django.conf import settings
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django.utils.functional import empty

if TYPE_CHECKING:
    from ...account.models import User
    from ...app.models import App
    from .dataloaders import DataLoader


class SaleorContext(HttpRequest):
    _cached_user: "User | None"
    decoded_auth_token: dict[str, Any] | None
    allow_replica: bool = True
    dataloaders: dict[str, "DataLoader"]
    app: "App | None"
    user: "User | None"  # type: ignore[assignment]
    requestor: "App | User | None"
    request_time: datetime.datetime

    def __init__(self, *args, **kwargs):
        if "dataloaders" in kwargs:
            self.dataloaders = kwargs.pop("dataloaders")
        super().__init__(*args, **kwargs)


def disallow_replica_in_context(context: SaleorContext) -> None:
    """Set information in context to use database replicas or not.

    Part of the database read replicas in Saleor.
    When Saleor builds a response for mutation `context` stores information
    `allow_replica=False`. That means that all data should be provided from
    the master database.
    When Saleor builds a response for query, set `allow_replica`=True in `context`.
    That means that all data should be provided from reading replica of the database.
    Database read replica couldn't be used to save any data.
    """
    context.allow_replica = False


def get_database_connection_name(context: SaleorContext) -> str:
    """Retrieve connection name based on request context.

    Part of the database read replicas in Saleor.
    Return proper connection name based on `context`.
    For more info check `disallow_replica_in_context`
    Add `.using(connection_name)` to use connection name in QuerySet.
    Queryset to main database: `User.objects.all()`.
    Queryset to read replica: `User.objects.using(connection_name).all()`.
    """
    allow_replica = getattr(context, "allow_replica", True)
    if allow_replica:
        return settings.DATABASE_CONNECTION_REPLICA_NAME
    return settings.DATABASE_CONNECTION_DEFAULT_NAME


def setup_context_user(context: SaleorContext) -> None:
    if hasattr(context.user, "_wrapped") and (
        context.user._wrapped is empty or context.user._wrapped is None  # type: ignore[union-attr]
    ):
        context.user._setup()  # type: ignore[union-attr]
        context.user = context.user._wrapped  # type: ignore[union-attr]


N = TypeVar("N")


@dataclass
class BaseContext[N]:
    node: N


@dataclass
class SyncWebhookControlContext(BaseContext[N]):
    allow_sync_webhooks: bool = True

    def __init__(self, node: N, allow_sync_webhooks: bool = True):
        self.node = node
        self.allow_sync_webhooks = allow_sync_webhooks


@dataclass
class ChannelContext(BaseContext[N]):
    channel_slug: str | None


M = TypeVar("M", bound=Model)


@dataclass
class ChannelQsContext(Generic[M]):
    qs: QuerySet[M]
    channel_slug: str | None
