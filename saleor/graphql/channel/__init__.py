from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

from django.db.models import QuerySet

N = TypeVar("N")


@dataclass
class ChannelContext(Generic[N]):
    node: N
    channel_slug: Optional[str]


@dataclass
class ChannelQsContext:
    qs: QuerySet
    channel_slug: Optional[str]
