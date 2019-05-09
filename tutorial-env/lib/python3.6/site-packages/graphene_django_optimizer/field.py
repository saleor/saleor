from graphene.types.field import Field
from graphene.types.unmountedtype import UnmountedType

from .hints import OptimizationHints


def field(field_type, *args, **kwargs):
    if isinstance(field_type, UnmountedType):
        field_type = Field.mounted(field_type)

    optimization_hints = OptimizationHints(*args, **kwargs)
    get_resolver = field_type.get_resolver

    def get_optimized_resolver(parent_resolver):
        resolver = get_resolver(parent_resolver)
        resolver.optimization_hints = optimization_hints
        return resolver

    field_type.get_resolver = get_optimized_resolver
    return field_type
