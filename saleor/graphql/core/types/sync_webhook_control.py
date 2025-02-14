from typing import Generic, TypeVar

from django.db.models import Model
from graphene.types.resolver import get_default_resolver

from .. import ResolveInfo
from ..context import SyncWebhookControlContext
from . import BaseObjectType
from .model import ModelObjectType

N = TypeVar("N")


class SyncWebhookControlContextObjectType(Generic[N], BaseObjectType):
    class Meta:
        abstract = True

    @staticmethod
    def resolver_with_context(
        attname,
        default_value,
        root: SyncWebhookControlContext[N],
        info: ResolveInfo,
        **args,
    ):
        resolver = get_default_resolver()
        return resolver(attname, default_value, root.node, info, **args)


T = TypeVar("T", bound=Model)


class SyncWebhookControlContextModelObjectType(
    ModelObjectType[T], SyncWebhookControlContextObjectType[T]
):
    class Meta:
        abstract = True
