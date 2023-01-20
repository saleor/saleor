from enum import Enum
from typing import Dict, List, Optional, Union

from graphene.utils.str_converters import to_snake_case
from graphql import get_default_backend, validate
from graphql.error import GraphQLSyntaxError
from graphql.language.ast import (
    Document,
    Field,
    FragmentDefinition,
    FragmentSpread,
    InlineFragment,
    OperationDefinition,
)


class IsFragment(Enum):
    TRUE = True
    FALSE = False


def get_events_from_subscription(query: str) -> List[str]:
    from ..api import schema

    graphql_backend = get_default_backend()
    try:
        document = graphql_backend.document_from_string(schema, query)
    except GraphQLSyntaxError:
        return []

    ast = document.document_ast
    validation_errors = validate(schema, ast)

    if validation_errors:
        return []

    subscription = get_subscription(ast)
    if not subscription:
        return []

    event_type = get_event_type_from_subscription(subscription)
    if not event_type:
        return []

    events_and_fragments: Dict[str, IsFragment] = get_events_from_field(event_type)
    if not events_and_fragments:
        return []

    fragment_definitions = get_fragment_definitions(ast)
    unpacked_events: Dict[str, IsFragment] = {}
    for event_name, is_fragment in events_and_fragments.items():
        if not is_fragment.value:
            continue
        event_definition = fragment_definitions[event_name]
        unpacked_events.update(get_events_from_field(event_definition))
    events_and_fragments.update(unpacked_events)

    events = [k for k, v in events_and_fragments.items() if not v == IsFragment.TRUE]
    return list(map(to_snake_case, events))


def get_subscription(ast: Document) -> Optional[OperationDefinition]:
    for definition in ast.definitions:
        if hasattr(definition, "operation") and definition.operation == "subscription":
            return definition
    return None


def get_event_type_from_subscription(
    subscription: OperationDefinition,
) -> Optional[Field]:
    for field in subscription.selection_set.selections:
        if field.name.value == "event" and isinstance(field, Field):
            return field
    return None


def get_events_from_field(
    field: Union[Field, FragmentDefinition]
) -> Dict[str, IsFragment]:
    events: Dict[str, IsFragment] = {}
    if field.selection_set:
        for field in field.selection_set.selections:
            if isinstance(field, InlineFragment) and field.type_condition:
                events[field.type_condition.name.value] = IsFragment.FALSE
            if isinstance(field, FragmentSpread):
                events[field.name.value] = IsFragment.TRUE
        return events
    return events


def get_fragment_definitions(ast: Document) -> Dict[str, FragmentDefinition]:
    fragments: Dict[str, FragmentDefinition] = {}
    for definition in ast.definitions:
        if isinstance(definition, FragmentDefinition):
            fragments[definition.name.value] = definition
    return fragments
