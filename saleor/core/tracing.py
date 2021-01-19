from functools import partial

from graphene.relay import GlobalID
from graphene.types.resolver import default_resolver
from graphql import ResolveInfo

DEFAULT_RESOLVERS = {default_resolver, GlobalID.id_resolver}


def should_trace(info: ResolveInfo) -> bool:
    if info.field_name not in info.parent_type.fields:
        return False

    resolver = info.parent_type.fields[info.field_name].resolver
    return not (
        resolver is None
        or is_default_resolver(resolver)
        or is_introspection_field(info)
    )


def is_introspection_field(info: ResolveInfo):
    if info.path is not None:
        for path in info.path:
            if isinstance(path, str) and path.startswith("__"):
                return True
    return False


def is_default_resolver(resolver):
    while isinstance(resolver, partial):
        resolver = resolver.func
        if resolver in DEFAULT_RESOLVERS:
            return True
    return resolver in DEFAULT_RESOLVERS
