import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from django.conf import settings
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django.utils.functional import empty
from graphql import GraphQLError

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
    """Replace the lazy ``context.user`` proxy with the resolved user object.

    Resolve the ``SimpleLazyObject`` if it has not been accessed yet, then unwrap
    it unconditionally. Unwrapping only in the ``empty``/``None`` case leaves the
    proxy in place whenever something (e.g. the storefront-traffic guard) already
    forced authentication earlier in the request, so downstream code would see a
    ``SimpleLazyObject`` instead of a plain ``User``.
    """
    if hasattr(context.user, "_wrapped"):
        if context.user._wrapped is empty:  # type: ignore[union-attr]
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


TEMPORARILY_UNAVAILABLE_ERROR_MESSAGE = (
    "Requested object is temporarily unavailable, please try again later."
)


class TemporarilyUnavailableError(GraphQLError):
    """A referenced object exists but cannot be served right now.

    The class name is exposed to clients as ``extensions.exception.code`` by
    ``format_error``, giving them a stable code to detect and retry on.
    """

    def __init__(self, message: str = TEMPORARILY_UNAVAILABLE_ERROR_MESSAGE):
        super().__init__(message)


def to_channel_context[T](
    node: T | None, channel_slug: str | None
) -> ChannelContext[T]:
    """Wrap a node in ``ChannelContext``, failing clearly when the node is missing.

    A dataloader can miss a row that certainly existed a moment ago, e.g. when a
    read replica lags behind the writer. Raise a clean, retryable error instead
    of crashing on ``None`` in ``is_type_of`` or silently returning ``null`` as
    if the relation was empty.
    """
    if node is None:
        raise TemporarilyUnavailableError()
    return ChannelContext(node=node, channel_slug=channel_slug)


M = TypeVar("M", bound=Model)


@dataclass
class ChannelQsContext(Generic[M]):
    qs: QuerySet[M]
    channel_slug: str | None
