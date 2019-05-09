"""
GraphQL.js provides a reference implementation for the GraphQL specification
but is also a useful utility for operating on GraphQL files and building
sophisticated tools.

This primary module exports a general purpose function for fulfilling all
steps of the GraphQL specification in a single operation, but also includes
utilities for every part of the GraphQL specification:

  - Parsing the GraphQL language.
  - Building a GraphQL type schema.
  - Validating a GraphQL request against a type schema.
  - Executing a GraphQL request against a type schema.

This also includes utility functions for operating on GraphQL types and
GraphQL documents to facilitate building tools.

You may also import from each sub-directory directly. For example, the
following two import statements are equivalent:

    from graphql import parse
    from graphql.language.base import parse
"""
from .pyutils.version import get_version

# The primary entry point into fulfilling a GraphQL request.
from .graphql import graphql

# Create and operate on GraphQL type definitions and schema.
from .type import (  # no import order
    GraphQLSchema,
    # Definitions
    GraphQLScalarType,
    GraphQLObjectType,
    GraphQLInterfaceType,
    GraphQLUnionType,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLField,
    GraphQLInputObjectField,
    GraphQLArgument,
    # "Enum" of Type Kinds
    TypeKind,
    # "Enum" of Directive locations
    DirectiveLocation,
    # Scalars
    GraphQLInt,
    GraphQLFloat,
    GraphQLString,
    GraphQLBoolean,
    GraphQLID,
    # Directive definition
    GraphQLDirective,
    # Built-in directives defined by the Spec
    specified_directives,
    GraphQLSkipDirective,
    GraphQLIncludeDirective,
    GraphQLDeprecatedDirective,
    # Constant Deprecation Reason
    DEFAULT_DEPRECATION_REASON,
    # GraphQL Types for introspection.
    __Schema,
    __Directive,
    __DirectiveLocation,
    __Type,
    __Field,
    __InputValue,
    __EnumValue,
    __TypeKind,
    # Meta-field definitions.
    SchemaMetaFieldDef,
    TypeMetaFieldDef,
    TypeNameMetaFieldDef,
    # Predicates
    is_type,
    is_input_type,
    is_output_type,
    is_leaf_type,
    is_composite_type,
    is_abstract_type,
    # Un-modifiers
    get_nullable_type,
    get_named_type,
)

# Parse and operate on GraphQL language source files.
from .language.base import (  # no import order
    Source,
    get_location,
    # Parse
    parse,
    parse_value,
    # Print
    print_ast,
    # Visit
    visit,
    ParallelVisitor,
    TypeInfoVisitor,
    BREAK,
)

# Execute GraphQL queries.
from .execution import (  # no import order
    execute,
    subscribe,
    ResolveInfo,
    MiddlewareManager,
    middlewares,
)

# Validate GraphQL queries.
from .validation import validate, specified_rules  # no import order

# Create and format GraphQL errors.
from .error import GraphQLError, format_error

# Utilities for operating on GraphQL type schema and parsed sources.
from .utils.base import (
    # The GraphQL query recommended for a full schema introspection.
    introspection_query,
    # Gets the target Operation from a Document
    get_operation_ast,
    # Build a GraphQLSchema from an introspection result.
    build_client_schema,
    # Build a GraphQLSchema from a parsed GraphQL Schema language AST.
    build_ast_schema,
    # Extends an existing GraphQLSchema from a parsed GraphQL Schema
    # language AST.
    extend_schema,
    # Print a GraphQLSchema to GraphQL Schema language.
    print_schema,
    # Create a GraphQLType from a GraphQL language AST.
    type_from_ast,
    # Create a JavaScript value from a GraphQL language AST.
    value_from_ast,
    # Create a GraphQL language AST from a JavaScript value.
    ast_from_value,
    # A helper to use within recursive-descent visitors which need to be aware of
    # the GraphQL type system.
    TypeInfo,
    # Determine if JavaScript values adhere to a GraphQL type.
    is_valid_value,
    # Determine if AST values adhere to a GraphQL type.
    is_valid_literal_value,
    # Concatenates multiple AST together.
    concat_ast,
    # Comparators for types
    is_equal_type,
    is_type_sub_type_of,
    do_types_overlap,
    # Asserts a string is a valid GraphQL name.
    assert_valid_name,
    # Undefined const
    Undefined,
)

# Utilities for dynamic execution engines
from .backend import (
    GraphQLBackend,
    GraphQLDocument,
    GraphQLCoreBackend,
    GraphQLDeciderBackend,
    GraphQLCachedBackend,
    get_default_backend,
    set_default_backend,
)

VERSION = (2, 1, 0, "final", 0)
__version__ = get_version(VERSION)


__all__ = (
    "__version__",
    "graphql",
    "GraphQLBoolean",
    "GraphQLEnumType",
    "GraphQLEnumValue",
    "GraphQLFloat",
    "GraphQLID",
    "GraphQLInputObjectType",
    "GraphQLInt",
    "GraphQLInterfaceType",
    "GraphQLList",
    "GraphQLNonNull",
    "GraphQLField",
    "GraphQLInputObjectField",
    "GraphQLArgument",
    "GraphQLObjectType",
    "GraphQLScalarType",
    "GraphQLSchema",
    "GraphQLString",
    "GraphQLUnionType",
    "GraphQLDirective",
    "specified_directives",
    "GraphQLSkipDirective",
    "GraphQLIncludeDirective",
    "GraphQLDeprecatedDirective",
    "DEFAULT_DEPRECATION_REASON",
    "TypeKind",
    "DirectiveLocation",
    "__Schema",
    "__Directive",
    "__DirectiveLocation",
    "__Type",
    "__Field",
    "__InputValue",
    "__EnumValue",
    "__TypeKind",
    "SchemaMetaFieldDef",
    "TypeMetaFieldDef",
    "TypeNameMetaFieldDef",
    "get_named_type",
    "get_nullable_type",
    "is_abstract_type",
    "is_composite_type",
    "is_input_type",
    "is_leaf_type",
    "is_output_type",
    "is_type",
    "BREAK",
    "ParallelVisitor",
    "Source",
    "TypeInfoVisitor",
    "get_location",
    "parse",
    "parse_value",
    "print_ast",
    "visit",
    "execute",
    "subscribe",
    "ResolveInfo",
    "MiddlewareManager",
    "middlewares",
    "specified_rules",
    "validate",
    "GraphQLError",
    "format_error",
    "TypeInfo",
    "assert_valid_name",
    "ast_from_value",
    "build_ast_schema",
    "build_client_schema",
    "concat_ast",
    "do_types_overlap",
    "extend_schema",
    "get_operation_ast",
    "introspection_query",
    "is_equal_type",
    "is_type_sub_type_of",
    "is_valid_literal_value",
    "is_valid_value",
    "print_schema",
    "type_from_ast",
    "value_from_ast",
    "get_version",
    "Undefined",
    "GraphQLBackend",
    "GraphQLDocument",
    "GraphQLCoreBackend",
    "GraphQLDeciderBackend",
    "GraphQLCachedBackend",
    "get_default_backend",
    "set_default_backend",
)
