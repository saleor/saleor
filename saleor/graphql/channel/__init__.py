from dataclasses import dataclass
from typing import Any, Optional

from django.db.models import QuerySet


@dataclass
class ChannelContext:
    node: Any
    channel_slug: Optional[str] = None


@dataclass
class ChannelQsContext:
    qs: QuerySet
    channel_slug: str
