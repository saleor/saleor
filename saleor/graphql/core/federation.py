from collections import defaultdict

from django.conf import settings
from graphene.utils.str_converters import to_snake_case
from graphene_federation import build_schema
from graphene_federation.entity import custom_entities
from graphql import GraphQLError

from ..channel import ChannelContext


def build_federated_schema(query=None, mutation=None, **kwargs):
    schema = build_schema(query, mutation, **kwargs)
    set_entity_resolver(schema)
    set_entity_type_resolver(schema)
    return schema


def set_entity_resolver(schema):
    """Set type resolver aware of ChannelContext on _Entity union."""
    entity = schema.get_type("Query")
    entity.fields["_entities"].resolver = resolve_entities


def resolve_entities(parent, info, representations):
    max_representations = settings.FEDERATED_QUERY_MAX_ENTITIES
    if max_representations and len(representations) > max_representations:
        representations_count = len(representations)
        raise GraphQLError(
            f"Federated query exceeded entity limit: {representations_count} "
            "items requested over {max_representations}."
        )

    resolvers = {}
    for representation in representations:
        if representation["__typename"] not in resolvers:
            try:
                model = custom_entities[representation["__typename"]]
                resolvers[representation["__typename"]] = getattr(
                    model, "_%s__resolve_references" % representation["__typename"]
                )
            except AttributeError as e:
                pass

    batches = defaultdict(list)
    for representation in representations:
        model = custom_entities[representation["__typename"]]
        model_arguments = representation.copy()
        typename = model_arguments.pop("__typename")
        model_arguments = {to_snake_case(k): v for k, v in model_arguments.items()}
        model_instance = model(**model_arguments)
        batches[typename].append(model_instance)

    entities = []
    for typename, batch in batches.items():
        if typename not in resolvers:
            continue

        resolver = resolvers[typename]
        entities.extend(resolver(batch, info))
    return entities


def set_entity_type_resolver(schema):
    """Set type resolver aware of ChannelContext on _Entity union."""
    entity = schema.get_type("_Entity")
    org_type_resolver = entity.resolve_type

    def resolve_entity_type(instance, info):
        if isinstance(instance, ChannelContext):
            return org_type_resolver(instance.node, info)

        return org_type_resolver(instance, info)

    entity.resolve_type = resolve_entity_type
