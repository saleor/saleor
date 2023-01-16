from typing import Dict, Optional

from graphene.utils.str_converters import to_snake_case
from graphql import parse, print_ast
from graphql.error.syntax_error import GraphQLSyntaxError
from graphql.language.ast import Document


def get_event_type_from_subscription(query: str) -> Optional[str]:
    try:
        ast = parse(query)
        subscription = None
        fragments = get_event_fragments_from_query(ast)

        for definition in ast.definitions:
            if (
                hasattr(definition, "operation")
                and definition.operation == "subscription"
            ):
                subscription = definition

        if subscription:
            subscription_string = print_ast(subscription)

            if fragments:
                for fragment_name, event_type in fragments.items():
                    if fragment_name in subscription_string:
                        return to_snake_case(event_type)

            event_type = (
                "".join(subscription_string.split())
                .split("event{...on")[1]
                .split("{")[0]
            )
            return to_snake_case(event_type)
        return None
    except (GraphQLSyntaxError, IndexError):
        return None


def get_event_fragments_from_query(ast: Document) -> Optional[Dict[str, str]]:
    fragments = {}
    for definition in ast.definitions:
        try:
            if (
                definition.__class__.__name__ == "FragmentDefinition"
                and definition.type_condition.name.value == "Event"
            ):
                fragment_string = print_ast(definition)
                event_type = (
                    "".join(fragment_string.split())
                    .split("Event{...on")[1]
                    .split("{")[0]
                )
                fragments[definition.name.value] = event_type
        except IndexError:
            continue
    return fragments
