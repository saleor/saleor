from typing import TypeVar, cast

from django.db.models import Model
from graphene.types.resolver import get_default_resolver

from ...translations.resolvers import resolve_translation
from .. import ResolveInfo
from ..context import ChannelContext
from .model import ModelObjectType

T = TypeVar("T", bound=Model)


class ChannelContextTypeForObjectType(ModelObjectType[T]):
    """A Graphene type that supports resolvers' root as ChannelContext objects."""

    class Meta:
        abstract = True

    @staticmethod
    def resolver_with_context(
        attname, default_value, root: ChannelContext, info: ResolveInfo, **args
    ):
        resolver = get_default_resolver()
        return resolver(attname, default_value, root.node, info, **args)

    @staticmethod
    def resolve_id(root: ChannelContext[T], _info: ResolveInfo):
        return root.node.pk

    @staticmethod
    def resolve_translation(
        root: ChannelContext[T], info: ResolveInfo, *, language_code
    ):
        # Resolver for TranslationField; needs to be manually specified.
        return resolve_translation(root.node, info, language_code=language_code)


class ChannelContextType(ChannelContextTypeForObjectType[T]):
    """A Graphene type that supports resolvers' root as ChannelContext objects."""

    class Meta:
        abstract = True

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
