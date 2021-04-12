from functools import partial

import opentracing
from graphene.relay import GlobalID
from graphene.types.resolver import default_resolver
from graphql import ResolveInfo

from ..graphql.channel.types import ChannelContextType, ChannelContextTypeWithMetadata
from ..graphql.meta.types import ObjectWithMetadata

IGNORED_RESOLVERS = {
    # Default resolvers:
    default_resolver,
    GlobalID.id_resolver,
    ChannelContextType.resolver_with_context,
    # Metadata resolvers:
    ChannelContextTypeWithMetadata.resolve_metadata,
    ChannelContextTypeWithMetadata.resolve_private_metadata,
    ObjectWithMetadata.resolve_metadata,
    ObjectWithMetadata.resolve_private_metadata,
}


def traced_resolver(func):
    def wrapper(*args, **kwargs):
        info = next(arg for arg in args if isinstance(arg, ResolveInfo))
        operation = f"{info.parent_type.name}.{info.field_name}"
        with opentracing.global_tracer().start_active_span(operation) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "graphql")
            span.set_tag("graphql.parent_type", info.parent_type.name)
            span.set_tag("graphql.field_name", info.field_name)
            return func(*args, **kwargs)

    return wrapper


def is_introspection_field(info: ResolveInfo):
    if info.path is not None:
        for path in info.path:
            if isinstance(path, str) and path.startswith("__"):
                return True
    return False


def is_resolver_ignored(resolver):
    while isinstance(resolver, partial):
        resolver = resolver.func
        if resolver in IGNORED_RESOLVERS:
            return True
    return resolver in IGNORED_RESOLVERS
