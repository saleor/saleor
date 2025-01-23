from dataclasses import dataclass
from typing import TypeVar

from django.db.models import QuerySet
from django.db.models.base import Model

from ..core.context import BaseContext

N = TypeVar("N", bound=Model)


@dataclass
class ChannelContext(BaseContext[N]):
    channel_slug: str | None


@dataclass
class ChannelQsContext:
    qs: QuerySet
    channel_slug: str | None
