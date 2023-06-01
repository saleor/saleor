from graphene.utils.str_converters import to_camel_case


def clean_predicate(predicate):
    """Convert camel cases keys into snake case."""
    if isinstance(predicate, list):
        return [
            clean_predicate(item) if isinstance(item, (dict, list)) else item
            for item in predicate
        ]
    return {
        to_camel_case(key): clean_predicate(value)
        if isinstance(value, (dict, list))
        else value
        for key, value in predicate.items()
    }
