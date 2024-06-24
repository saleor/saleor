from collections import defaultdict
from typing import Any

import graphene
from django.conf import settings
from graphene.utils.str_converters import to_snake_case
from graphql import GraphQLArgument, GraphQLError, GraphQLField, GraphQLList

from ...channel import ChannelContext
from ...schema_printer import print_schema
from .. import ResolveInfo
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


def build_federated_schema(
    query, mutation, types, subscription, directives=None
) -> graphene.Schema:
    """Create GraphQL schema that supports Apollo Federation."""
    schema = graphene.Schema(
        query=query,
        mutation=mutation,
        types=list(types) + [_Any, _Entity, _Service],
        subscription=subscription,
        directives=directives,
    )

    entity_type = schema.get_type("_Entity")
    entity_type.resolve_type = create_entity_type_resolver(schema)

    query_type = schema.get_type("Query")
    query_type.fields["_entities"] = GraphQLField(
        GraphQLList(entity_type),
        args={
            "representations": GraphQLArgument(
                GraphQLList(schema.get_type("_Any")),
            ),
        },
        resolver=resolve_entities,
    )
    query_type.fields["_service"] = GraphQLField(
        schema.get_type("_Service"),
        resolver=create_service_sdl_resolver(schema),
    )

    return schema


def create_entity_type_resolver(schema):
    """Create type resolver aware of ChannelContext on _Entity union."""

    def resolve_entity_type(instance, info: ResolveInfo):
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

    return resolve_entity_type


def resolve_entities(_, info: ResolveInfo, *, representations):
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
                model = federated_entities[representation["__typename"]]
                resolvers[representation["__typename"]] = getattr(
                    model,
                    "_{}__resolve_references".format(representation["__typename"]),
                )
            except AttributeError:
                pass

    batches = defaultdict(list)
    for representation in representations:
        model = federated_entities[representation["__typename"]]
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


def create_service_sdl_resolver(schema):
    # subscriptions are not handled by the federation protocol
    schema_sans_subscriptions = graphene.Schema(
        query=schema._query,
        mutation=schema._mutation,
        types=schema.types,
        directives=schema._directives,
    )
    # Render schema to string
    federated_schema_sdl = print_schema(schema_sans_subscriptions)

    del schema_sans_subscriptions

    # Remove "schema { ... }"
    schema_start = federated_schema_sdl.find("schema {")
    schema_end = federated_schema_sdl.find("}", schema_start) + 1
    federated_schema_sdl = (
        federated_schema_sdl[:schema_start] + federated_schema_sdl[schema_end:]
    ).lstrip()

    # Append "@key" to federated types
    for type_name, graphql_type in federated_entities.items():
        type_sdl = f"type {type_name} "
        type_start = federated_schema_sdl.find(type_sdl)
        type_fields_open = federated_schema_sdl.find("{", type_start)
        federated_schema_sdl = (
            federated_schema_sdl[:type_fields_open]
            + getattr(graphql_type, "_sdl")
            + " "
            + federated_schema_sdl[type_fields_open:]
        )

    def resolve_service_sdl(_root, _info: ResolveInfo):
        return {"sdl": federated_schema_sdl}

    return resolve_service_sdl
