from graphql.error import GraphQLError


def validate_one_of_args_is_in_query(arg1_name, arg1, arg2_name, arg2):
    if arg1 and arg2:
        raise GraphQLError(
            f"Argument '{arg1_name}' cannot be combined with '{arg2_name}'"
        )
    if not arg1 and not arg2:
        raise GraphQLError(
            f"Either '{arg1_name}'  or '{arg2_name}' argument is required"
        )
