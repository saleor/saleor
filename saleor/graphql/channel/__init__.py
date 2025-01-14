from dataclasses import dataclass
from typing import Generic, TypeVar

from django.db.models import QuerySet

N = TypeVar("N")


@dataclass
class ChannelContext(Generic[N]):
    node: N
    channel_slug: str | None


@dataclass
class ChannelQsContext:
    qs: QuerySet
    channel_slug: str | None
