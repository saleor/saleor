from typing import Generic, TypeVar, cast

from django.db.models import Model
from graphene.types.resolver import get_default_resolver

from ...translations.resolvers import resolve_translation
from .. import ResolveInfo
from ..context import ChannelContext
from .base import BaseObjectType
from .model import ModelObjectType

N = TypeVar("N", bound=Model)


class ChannelContextTypeForObjectType(Generic[N], BaseObjectType):
    """A Graphene type that supports resolvers' root as ChannelContext objects."""

    class Meta:
        abstract = True

    @staticmethod
    def resolver_with_context(
        attname, default_value, root: ChannelContext[N], info: ResolveInfo, **args
    ):
        resolver = get_default_resolver()
        return resolver(attname, default_value, root.node, info, **args)

    @staticmethod
    def resolve_translation(
        root: ChannelContext[N], info: ResolveInfo, *, language_code
    ):
        # Resolver for TranslationField; needs to be manually specified.
        return resolve_translation(root.node, info, language_code=language_code)


T = TypeVar("T", bound=Model)


class ChannelContextType(ChannelContextTypeForObjectType[T], ModelObjectType[T]):
    """A Graphene type that supports resolvers' root as ChannelContext objects."""

    class Meta:
        abstract = True

    @staticmethod
    def resolve_id(root: ChannelContext[T], _info: ResolveInfo):
        return root.node.pk

    @classmethod
    def is_type_of(cls, root: ChannelContext[T] | T, _info: ResolveInfo) -> bool:
        # Unwrap node from ChannelContext if it didn't happen already
        if isinstance(root, ChannelContext):
            root = root.node

        if isinstance(root, cls):
            return True

        if cls._meta.model._meta.proxy:
            model = root._meta.model
        else:
            model = cast(type[Model], root._meta.model._meta.concrete_model)
        return model == cls._meta.model
