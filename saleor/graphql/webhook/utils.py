from typing import Dict, List, Optional

from graphene.utils.str_converters import to_snake_case
from graphql import parse
from graphql.error import GraphQLSyntaxError
from graphql.language.ast import Document


def get_event_type_from_subscription(query: str) -> List[str]:
    try:
        ast = parse(query)
        subscription = get_subscription(ast)
        if not subscription:
            return []

        event_field = get_event_field_from_subscription(subscription)
        if not event_field:
            return []

        events = get_events(event_field)
        if not events:
            return []

        fragments = get_event_fragment_names_from_query(ast)
        if fragments:
            events = [fragments.get(event, event) for event in events]

        return list(map(to_snake_case, events))

    except GraphQLSyntaxError:
        return []


def get_event_field_from_subscription(field):
    if hasattr(field, "selection_set"):
        fields = field.selection_set.selections
        for f in fields:
            if f.name.value == "event":
                return f
            get_event_field_from_subscription(f)


def get_subscription(ast):
    for definition in ast.definitions:
        if hasattr(definition, "operation") and definition.operation == "subscription":
            return definition
    return None


def get_events(field):
    try:
        fields = field.selection_set.selections
        events = []
        for field in fields:
            if hasattr(field, "name"):
                events.append(field.name.value)
            if hasattr(field, "type_condition"):
                events.append(field.type_condition.name.value)
        return events
    except AttributeError:
        return []


def get_event_fragment_names_from_query(ast: Document) -> Optional[Dict[str, str]]:
    fragments = {}
    try:
        for definition in ast.definitions:
            if (
                definition.__class__.__name__ == "FragmentDefinition"
                and definition.type_condition.name.value == "Event"
            ):
                event = definition.selection_set.selections[0].type_condition.name.value
                fragments[definition.name.value] = event
        return fragments
    except AttributeError:
        return fragments
