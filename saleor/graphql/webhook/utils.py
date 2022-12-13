from graphene.utils.str_converters import to_snake_case
from graphql import parse, print_ast


def get_event_type_from_subscription(query: str):
    try:
        ast = parse(query)
        subscription = None
        for definition in ast.definitions:
            if definition.operation == "subscription":
                subscription = definition

        if subscription:
            subscription_string = print_ast(subscription)
            event_type = (
                subscription_string.replace(" ", "").split("...on")[1].split("{")[0]
            )
            return to_snake_case(event_type)
        return None
    except Exception:
        return None
