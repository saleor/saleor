from typing import Dict, List, Optional

from graphene.utils.str_converters import to_snake_case
from graphql import parse
from graphql.error import GraphQLSyntaxError
from graphql.language.ast import (
    Document,
    Field,
    FragmentDefinition,
    FragmentSpread,
    InlineFragment,
    Node,
    OperationDefinition,
)


def get_event_type_from_subscription(query: str) -> List[str]:
    try:
        ast = parse(query)
    except GraphQLSyntaxError:
        return []
    breakpoint()
    subscription = get_subscription(ast)
    if not subscription:
        return []

    event_field = get_event_field_from_subscription(subscription)
    if not event_field:
        return []

    events = get_events(event_field)
    if not events:
        return []

    # fragments = get_event_fragment_names_from_query(ast)
    # if fragments:
    #     events = [fragments.get(event, event) for event in events]

    return list(map(to_snake_case, events))


def get_event_field_from_subscription(field: Node) -> Optional[Field]:
    if hasattr(field, "selection_set") and field.selection_set:
        fields = field.selection_set.selections
        for f in fields:
            if f.name.value == "event" and isinstance(f, Field):
                return f
            get_event_field_from_subscription(f)
    return None


def get_fragments_from_field(field: Node, fragments) -> Dict[str, FragmentSpread]:
    if hasattr(field, "selection_set") and field.selection_set:
        fields = field.selection_set.selections
        for f in fields:
            if isinstance(f, FragmentSpread):
                fragments[f.name.value] = f
            else:
                get_fragments_from_field(f, fragments)
    return fragments


def get_subscription(ast: Document) -> Optional[OperationDefinition]:
    for definition in ast.definitions:
        if hasattr(definition, "operation") and definition.operation == "subscription":
            return definition
    return None


def get_events(field: Field) -> Dict[str, str]:
    events: Dict[str, str] = {}
    if field.selection_set:
        for field in field.selection_set.selections:
            if isinstance(field, InlineFragment) and field.type_condition:
                events[field.type_condition.name.value] = "event"
            if isinstance(field, FragmentSpread):
                events[field.name.value] = "fragment"
        return events
    return events


def get_event_fragment_names_from_query(ast: Document) -> Optional[Dict[str, str]]:
    fragments = {}
    try:
        for definition in ast.definitions:
            if (
                isinstance(definition, FragmentDefinition)
                and definition.type_condition
                and definition.type_condition.name.value == "Event"
            ):
                event = definition.selection_set.selections[0].type_condition.name.value
                fragments[definition.name.value] = event
        return fragments
    except AttributeError:
        return fragments
