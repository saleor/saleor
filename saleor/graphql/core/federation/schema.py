from collections import defaultdict
from typing import Any

import graphene
from django.conf import settings
from graphene.utils.str_converters import to_snake_case
#from graphene_federation import build_schema
#from graphene_federation.entity import custom_entities
from graphql import GraphQLArgument, GraphQLError, GraphQLField, GraphQLList

from ...channel import ChannelContext
from .entities import federated_entities


class _Any(graphene.Scalar):
    """_Any value scalar as defined by Federation spec."""

    __typename = graphene.String(required=True)

    @staticmethod
    def serialize(any_value: Any):
        return any_value

    @staticmethod
    def parse_literal(any_value: Any):
        raise any_value

    @staticmethod
    def parse_value(any_value: Any):
        return any_value


class _Entity(graphene.Union):
    """_Entity union as defined by Federation spec."""

    class Meta:
        types = tuple(federated_entities.values())


class _Service(graphene.ObjectType):
    """_Service manifest as defined by Federation spec."""

    sdl = graphene.String()


def build_federated_schema(query=None, mutation=None, types=None):
    """Creates GraphQL schema that supports Apollo Federation"""
    schema = graphene.Schema(
        query=query,
        mutation=mutation,
        types=list(types) + [_Any, _Entity, _Service],
    )

    query_type = schema.get_type("Query")
    query_type.fields["_entities"] = GraphQLField(
        GraphQLList(schema.get_type("_Entity")),
        args={
            "representations": GraphQLArgument(
                GraphQLList(schema.get_type("_Any")),
            ),
        },
        resolver=resolve_entities,
    )
    query_type.fields["_service"] = GraphQLField(
        schema.get_type("_Service"),
        resolver=resolve_service_sdl,
    )

    return schema


def _build_federated_schema(query=None, mutation=None, **kwargs):
    schema = build_schema(query, mutation, **kwargs)
    #set_entity_resolver(schema)
    #set_entity_type_resolver(schema)
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
            f"items requested over {max_representations}."
        )

    resolvers = {}
    for representation in representations:
        if representation["__typename"] not in resolvers:
            try:
                model = custom_entities[representation["__typename"]]
                resolvers[representation["__typename"]] = getattr(
                    model, "_%s__resolve_references" % representation["__typename"]
                )
            except AttributeError:
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

    def resolve_entity_type(instance, info):
        # Use new strategy to resolve GraphQL Type for `ObjectType`
        if isinstance(instance, ChannelContext):
            model = type(instance.node)
        else:
            model = type(instance)

        model_type = schema.get_type(model._meta.object_name)
        if model_type is None:
            raise ValueError(
                f"GraphQL type for model {model} could not be found. "
                "This is caused by federated type missing get_model method."
            )

        return model_type

    entity.resolve_type = resolve_entity_type


def resolve_service_sdl(*_args):
    sdl = []
    for graphql_type in federated_entities.values():
        print(getattr(graphql_type, "_sdl"))

    return {"sdl": "\n".join(sdl)}
