from functools import partial

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


def should_trace(info: ResolveInfo) -> bool:
    if info.field_name not in info.parent_type.fields:
        return False

    resolver = info.parent_type.fields[info.field_name].resolver
    return not (
        resolver is None
        or is_resolver_ignored(resolver)
        or is_introspection_field(info)
    )


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
