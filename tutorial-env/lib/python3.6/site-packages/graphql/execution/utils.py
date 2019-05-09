# -*- coding: utf-8 -*-
import logging
from traceback import format_exception

from ..error import GraphQLError
from ..language import ast
from ..pyutils.default_ordered_dict import DefaultOrderedDict
from ..type.definition import GraphQLInterfaceType, GraphQLUnionType
from ..type.directives import GraphQLIncludeDirective, GraphQLSkipDirective
from ..type.introspection import (
    SchemaMetaFieldDef,
    TypeMetaFieldDef,
    TypeNameMetaFieldDef,
)
from ..utils.type_from_ast import type_from_ast
from .values import get_argument_values, get_variable_values

# Necessary for static type checking
if False:  # flake8: noqa
    from ..type.definition import GraphQLObjectType, GraphQLField
    from ..type.schema import GraphQLSchema
    from ..language.ast import (
        Document,
        OperationDefinition,
        SelectionSet,
        Directive,
        FragmentDefinition,
        InlineFragment,
        Field,
    )
    from .base import ResolveInfo
    from types import TracebackType
    from typing import Any, List, Dict, Optional, Union, Callable, Set, Tuple

logger = logging.getLogger(__name__)


class ExecutionContext(object):
    """Data that must be available at all points during query execution.

    Namely, schema of the type system that is currently executing,
    and the fragments defined in the query document"""

    __slots__ = (
        "schema",
        "fragments",
        "root_value",
        "operation",
        "variable_values",
        "errors",
        "context_value",
        "argument_values_cache",
        "executor",
        "middleware",
        "allow_subscriptions",
        "_subfields_cache",
    )

    def __init__(
        self,
        schema,  # type: GraphQLSchema
        document_ast,  # type: Document
        root_value,  # type: Any
        context_value,  # type: Any
        variable_values,  # type: Optional[Dict[str, Any]]
        operation_name,  # type: Optional[str]
        executor,  # type: Any
        middleware,  # type: Optional[Any]
        allow_subscriptions,  # type: bool
    ):
        # type: (...) -> None
        """Constructs a ExecutionContext object from the arguments passed
        to execute, which we will pass throughout the other execution
        methods."""
        errors = []  # type: List[Exception]
        operation = None
        fragments = {}  # type: Dict[str, FragmentDefinition]

        for definition in document_ast.definitions:
            if isinstance(definition, ast.OperationDefinition):
                if not operation_name and operation:
                    raise GraphQLError(
                        "Must provide operation name if query contains multiple operations."
                    )

                if (
                    not operation_name
                    or definition.name
                    and definition.name.value == operation_name
                ):
                    operation = definition

            elif isinstance(definition, ast.FragmentDefinition):
                fragments[definition.name.value] = definition

            else:
                raise GraphQLError(
                    u"GraphQL cannot execute a request containing a {}.".format(
                        definition.__class__.__name__
                    ),
                    definition,
                )

        if not operation:
            if operation_name:
                raise GraphQLError(
                    u'Unknown operation named "{}".'.format(operation_name)
                )

            else:
                raise GraphQLError("Must provide an operation.")

        variable_values = get_variable_values(
            schema, operation.variable_definitions or [], variable_values
        )

        self.schema = schema
        self.fragments = fragments
        self.root_value = root_value
        self.operation = operation
        self.variable_values = variable_values
        self.errors = errors
        self.context_value = context_value
        self.argument_values_cache = {}  # type: Dict[Tuple[GraphQLField, Field], Dict[str, Any]]
        self.executor = executor
        self.middleware = middleware
        self.allow_subscriptions = allow_subscriptions
        self._subfields_cache = {}  # type: Dict[Tuple[GraphQLObjectType, Tuple[Field, ...]], DefaultOrderedDict]

    def get_field_resolver(self, field_resolver):
        # type: (Callable) -> Callable
        if not self.middleware:
            return field_resolver
        return self.middleware.get_field_resolver(field_resolver)

    def get_argument_values(self, field_def, field_ast):
        # type: (GraphQLField, Field) -> Dict[str, Any]
        k = field_def, field_ast
        if k not in self.argument_values_cache:
            self.argument_values_cache[k] = get_argument_values(
                field_def.args, field_ast.arguments, self.variable_values
            )

        return self.argument_values_cache[k]

    def report_error(self, error, traceback=None):
        # type: (Exception, Optional[TracebackType]) -> None
        exception = format_exception(
            type(error), error, getattr(error, "stack", None) or traceback
        )
        logger.error("".join(exception))
        self.errors.append(error)

    def get_sub_fields(self, return_type, field_asts):
        # type: (GraphQLObjectType, List[Field]) -> DefaultOrderedDict
        k = return_type, tuple(field_asts)
        if k not in self._subfields_cache:
            subfield_asts = DefaultOrderedDict(list)
            visited_fragment_names = set()  # type: Set[str]
            for field_ast in field_asts:
                selection_set = field_ast.selection_set
                if selection_set:
                    subfield_asts = collect_fields(
                        self,
                        return_type,
                        selection_set,
                        subfield_asts,
                        visited_fragment_names,
                    )
            self._subfields_cache[k] = subfield_asts
        return self._subfields_cache[k]


class SubscriberExecutionContext(object):
    __slots__ = "exe_context", "errors"

    def __init__(self, exe_context):
        # type: (ExecutionContext) -> None
        self.exe_context = exe_context
        self.errors = []  # type: List[Exception]

    def reset(self):
        # type: () -> None
        self.errors = []

    def __getattr__(self, name):
        # type: (str) -> Any
        return getattr(self.exe_context, name)


def get_operation_root_type(schema, operation):
    # type: (GraphQLSchema, OperationDefinition) -> GraphQLObjectType
    op = operation.operation
    if op == "query":
        return schema.get_query_type()

    elif op == "mutation":
        mutation_type = schema.get_mutation_type()

        if not mutation_type:
            raise GraphQLError("Schema is not configured for mutations", [operation])

        return mutation_type

    elif op == "subscription":
        subscription_type = schema.get_subscription_type()

        if not subscription_type:
            raise GraphQLError(
                "Schema is not configured for subscriptions", [operation]
            )

        return subscription_type

    raise GraphQLError(
        "Can only execute queries, mutations and subscriptions", [operation]
    )


def collect_fields(
    ctx,  # type: ExecutionContext
    runtime_type,  # type: GraphQLObjectType
    selection_set,  # type: SelectionSet
    fields,  # type: DefaultOrderedDict
    prev_fragment_names,  # type: Set[str]
):
    # type: (...) -> DefaultOrderedDict
    """
    Given a selectionSet, adds all of the fields in that selection to
    the passed in map of fields, and returns it at the end.

    collect_fields requires the "runtime type" of an object. For a field which
    returns and Interface or Union type, the "runtime type" will be the actual
    Object type returned by that field.
    """
    for selection in selection_set.selections:
        directives = selection.directives

        if isinstance(selection, ast.Field):
            if not should_include_node(ctx, directives):
                continue

            name = get_field_entry_key(selection)
            fields[name].append(selection)

        elif isinstance(selection, ast.InlineFragment):
            if not should_include_node(
                ctx, directives
            ) or not does_fragment_condition_match(ctx, selection, runtime_type):
                continue

            collect_fields(
                ctx, runtime_type, selection.selection_set, fields, prev_fragment_names
            )

        elif isinstance(selection, ast.FragmentSpread):
            frag_name = selection.name.value

            if frag_name in prev_fragment_names or not should_include_node(
                ctx, directives
            ):
                continue

            prev_fragment_names.add(frag_name)
            fragment = ctx.fragments[frag_name]
            frag_directives = fragment.directives
            if (
                not fragment
                or not should_include_node(ctx, frag_directives)
                or not does_fragment_condition_match(ctx, fragment, runtime_type)
            ):
                continue

            collect_fields(
                ctx, runtime_type, fragment.selection_set, fields, prev_fragment_names
            )

    return fields


def should_include_node(ctx, directives):
    # type: (ExecutionContext, Optional[List[Directive]]) -> bool
    """Determines if a field should be included based on the @include and
    @skip directives, where @skip has higher precidence than @include."""
    # TODO: Refactor based on latest code
    if directives:
        skip_ast = None

        for directive in directives:
            if directive.name.value == GraphQLSkipDirective.name:
                skip_ast = directive
                break

        if skip_ast:
            args = get_argument_values(
                GraphQLSkipDirective.args, skip_ast.arguments, ctx.variable_values
            )
            if args.get("if") is True:
                return False

        include_ast = None

        for directive in directives:
            if directive.name.value == GraphQLIncludeDirective.name:
                include_ast = directive
                break

        if include_ast:
            args = get_argument_values(
                GraphQLIncludeDirective.args, include_ast.arguments, ctx.variable_values
            )

            if args.get("if") is False:
                return False

    return True


def does_fragment_condition_match(
    ctx,  # type: ExecutionContext
    fragment,  # type: Union[FragmentDefinition, InlineFragment]
    type_,  # type: GraphQLObjectType
):
    # type: (...) -> bool
    type_condition_ast = fragment.type_condition
    if not type_condition_ast:
        return True

    conditional_type = type_from_ast(ctx.schema, type_condition_ast)
    if conditional_type.is_same_type(type_):
        return True

    if isinstance(conditional_type, (GraphQLInterfaceType, GraphQLUnionType)):
        return ctx.schema.is_possible_type(conditional_type, type_)

    return False


def get_field_entry_key(node):
    # type: (Field) -> str
    """Implements the logic to compute the key of a given field's entry"""
    if node.alias:
        return node.alias.value
    return node.name.value


def default_resolve_fn(source, info, **args):
    # type: (Any, ResolveInfo, **Any) -> Union[int, str]
    """If a resolve function is not given, then a default resolve behavior is used which takes the property of the source object
    of the same name as the field and returns it as the result, or if it's a function, returns the result of calling that function."""
    name = info.field_name
    property = getattr(source, name, None)
    if callable(property):
        return property()
    return property


def get_field_def(
    schema,  # type: GraphQLSchema
    parent_type,  # type: GraphQLObjectType
    field_name,  # type: str
):
    # type: (...) -> Optional[GraphQLField]
    """This method looks up the field on the given type defintion.
    It has special casing for the two introspection fields, __schema
    and __typename. __typename is special because it can always be
    queried as a field, even in situations where no other fields
    are allowed, like on a Union. __schema could get automatically
    added to the query type, but that would require mutating type
    definitions, which would cause issues."""
    if field_name == "__schema" and schema.get_query_type() == parent_type:
        return SchemaMetaFieldDef
    elif field_name == "__type" and schema.get_query_type() == parent_type:
        return TypeMetaFieldDef
    elif field_name == "__typename":
        return TypeNameMetaFieldDef
    return parent_type.fields.get(field_name)
