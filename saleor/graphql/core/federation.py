from graphene_federation import build_schema

from ..channel import ChannelContext


def build_federated_schema(query=None, mutation=None, **kwargs):
    schema = build_schema(query, mutation, **kwargs)
    set_entity_type_resolver(schema)
    return schema


def set_entity_type_resolver(schema):
    """Set type resolver aware of ChannelContext on _Entity union."""
    entity = schema.get_type("_Entity")
    org_type_resolver = entity.resolve_type

    def resolve_entity_type(instance, info):
        if isinstance(instance, ChannelContext):
            return org_type_resolver(instance.node, info)

        return org_type_resolver(instance, info)

    entity.resolve_type = resolve_entity_type
