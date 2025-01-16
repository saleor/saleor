from typing import TypeVar

from django.db.models import Model
from graphene.types.resolver import get_default_resolver

from .. import ResolveInfo
from ..context import SyncWebhookControlContext
from .model import ModelObjectType

T = TypeVar("T", bound=Model)


class SyncWebhookControlContextType(ModelObjectType[T]):
    class Meta:
        abstract = True

    @staticmethod
    def resolver_with_context(
        attname,
        default_value,
        root: SyncWebhookControlContext,
        info: ResolveInfo,
        **args,
    ):
        resolver = get_default_resolver()
        return resolver(attname, default_value, root.node, info, **args)
