import collections

from ..pyutils.ordereddict import OrderedDict
from ..utils.assert_valid_name import assert_valid_name
from .definition import GraphQLArgument, GraphQLNonNull, is_input_type
from .scalars import GraphQLBoolean, GraphQLString


class DirectiveLocation(object):
    # Operations
    QUERY = "QUERY"
    MUTATION = "MUTATION"
    SUBSCRIPTION = "SUBSCRIPTION"
    FIELD = "FIELD"
    FRAGMENT_DEFINITION = "FRAGMENT_DEFINITION"
    FRAGMENT_SPREAD = "FRAGMENT_SPREAD"
    INLINE_FRAGMENT = "INLINE_FRAGMENT"

    # Schema Definitions
    SCHEMA = "SCHEMA"
    SCALAR = "SCALAR"
    OBJECT = "OBJECT"
    FIELD_DEFINITION = "FIELD_DEFINITION"
    ARGUMENT_DEFINITION = "ARGUMENT_DEFINITION"
    INTERFACE = "INTERFACE"
    UNION = "UNION"
    ENUM = "ENUM"
    ENUM_VALUE = "ENUM_VALUE"
    INPUT_OBJECT = "INPUT_OBJECT"
    INPUT_FIELD_DEFINITION = "INPUT_FIELD_DEFINITION"

    OPERATION_LOCATIONS = [QUERY, MUTATION, SUBSCRIPTION]

    FRAGMENT_LOCATIONS = [FRAGMENT_DEFINITION, FRAGMENT_SPREAD, INLINE_FRAGMENT]

    FIELD_LOCATIONS = [FIELD]


class GraphQLDirective(object):
    __slots__ = "name", "args", "description", "locations"

    def __init__(self, name, description=None, args=None, locations=None):
        assert name, "Directive must be named."
        assert_valid_name(name)
        assert isinstance(
            locations, collections.Iterable
        ), "Must provide locations for directive."

        self.name = name
        self.description = description
        self.locations = locations

        if args:
            assert isinstance(
                args, collections.Mapping
            ), "{} args must be a dict with argument names as keys.".format(name)
            for arg_name, _arg in args.items():
                assert_valid_name(arg_name)
                assert is_input_type(
                    _arg.type
                ), "{}({}) argument type must be Input Type but got {}.".format(
                    name, arg_name, _arg.type
                )
        self.args = args or OrderedDict()


"""Used to conditionally include fields or fragments."""
GraphQLIncludeDirective = GraphQLDirective(
    name="include",
    description="Directs the executor to include this field or fragment only when the `if` argument is true.",
    args={
        "if": GraphQLArgument(
            type=GraphQLNonNull(GraphQLBoolean), description="Included when true."
        )
    },
    locations=[
        DirectiveLocation.FIELD,
        DirectiveLocation.FRAGMENT_SPREAD,
        DirectiveLocation.INLINE_FRAGMENT,
    ],
)

"""Used to conditionally skip (exclude) fields or fragments."""
GraphQLSkipDirective = GraphQLDirective(
    name="skip",
    description="Directs the executor to skip this field or fragment when the `if` argument is true.",
    args={
        "if": GraphQLArgument(
            type=GraphQLNonNull(GraphQLBoolean), description="Skipped when true."
        )
    },
    locations=[
        DirectiveLocation.FIELD,
        DirectiveLocation.FRAGMENT_SPREAD,
        DirectiveLocation.INLINE_FRAGMENT,
    ],
)

"""Constant string used for default reason for a deprecation."""
DEFAULT_DEPRECATION_REASON = "No longer supported"

"""Used to declare element of a GraphQL schema as deprecated."""
GraphQLDeprecatedDirective = GraphQLDirective(
    name="deprecated",
    description="Marks an element of a GraphQL schema as no longer supported.",
    args={
        "reason": GraphQLArgument(
            type=GraphQLString,
            description=(
                "Explains why this element was deprecated, usually also including a suggestion for how to"
                "access supported similar data. Formatted in [Markdown]"
                "(https://daringfireball.net/projects/markdown/)."
            ),
            default_value=DEFAULT_DEPRECATION_REASON,
        )
    },
    locations=[DirectiveLocation.FIELD_DEFINITION, DirectiveLocation.ENUM_VALUE],
)

specified_directives = [
    GraphQLIncludeDirective,
    GraphQLSkipDirective,
    GraphQLDeprecatedDirective,
]
