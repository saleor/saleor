from dataclasses import dataclass
from typing import Generic, Optional, TypeVar, Union

from django.db.models import QuerySet

N = TypeVar("N")


@dataclass
class ChannelContext(Generic[N]):
    channel_slug: Optional[str]
    node: Optional[N] = None
    node_id: Optional[Union[str, int]] = None


@dataclass
class ChannelQsContext:
    qs: QuerySet
    channel_slug: Optional[str]
