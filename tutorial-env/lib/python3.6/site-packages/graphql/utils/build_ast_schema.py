from ..execution.values import get_argument_values
from ..language import ast
from ..pyutils.ordereddict import OrderedDict
from ..type import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLDeprecatedDirective,
    GraphQLDirective,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLFloat,
    GraphQLID,
    GraphQLIncludeDirective,
    GraphQLInputObjectField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLSkipDirective,
    GraphQLString,
    GraphQLUnionType,
)
from ..type.introspection import (
    __Directive,
    __DirectiveLocation,
    __EnumValue,
    __Field,
    __InputValue,
    __Schema,
    __Type,
    __TypeKind,
)
from ..utils.value_from_ast import value_from_ast


def _build_wrapped_type(inner_type, input_type_ast):
    if isinstance(input_type_ast, ast.ListType):
        return GraphQLList(_build_wrapped_type(inner_type, input_type_ast.type))

    if isinstance(input_type_ast, ast.NonNullType):
        return GraphQLNonNull(_build_wrapped_type(inner_type, input_type_ast.type))

    return inner_type


def _get_inner_type_name(type_ast):
    if isinstance(type_ast, (ast.ListType, ast.NonNullType)):
        return _get_inner_type_name(type_ast.type)

    return type_ast.name.value


def _get_named_type_ast(type_ast):
    named_type = type_ast
    while isinstance(named_type, (ast.ListType, ast.NonNullType)):
        named_type = named_type.type

    return named_type


def _false(*_):
    return False


def _none(*_):
    return None


def build_ast_schema(document):
    assert isinstance(document, ast.Document), "must pass in Document ast."

    schema_def = None

    type_asts = (
        ast.ScalarTypeDefinition,
        ast.ObjectTypeDefinition,
        ast.InterfaceTypeDefinition,
        ast.EnumTypeDefinition,
        ast.UnionTypeDefinition,
        ast.InputObjectTypeDefinition,
    )

    type_defs = []
    directive_defs = []

    for d in document.definitions:
        if isinstance(d, ast.SchemaDefinition):
            if schema_def:
                raise Exception("Must provide only one schema definition.")
            schema_def = d
        if isinstance(d, type_asts):
            type_defs.append(d)
        elif isinstance(d, ast.DirectiveDefinition):
            directive_defs.append(d)

    if not schema_def:
        raise Exception("Must provide a schema definition.")

    query_type_name = None
    mutation_type_name = None
    subscription_type_name = None

    for operation_type in schema_def.operation_types:
        type_name = operation_type.type.name.value
        if operation_type.operation == "query":
            if query_type_name:
                raise Exception("Must provide only one query type in schema.")
            query_type_name = type_name
        elif operation_type.operation == "mutation":
            if mutation_type_name:
                raise Exception("Must provide only one mutation type in schema.")
            mutation_type_name = type_name
        elif operation_type.operation == "subscription":
            if subscription_type_name:
                raise Exception("Must provide only one subscription type in schema.")
            subscription_type_name = type_name

    if not query_type_name:
        raise Exception("Must provide schema definition with query type.")

    ast_map = {d.name.value: d for d in type_defs}

    if query_type_name not in ast_map:
        raise Exception(
            'Specified query type "{}" not found in document.'.format(query_type_name)
        )

    if mutation_type_name and mutation_type_name not in ast_map:
        raise Exception(
            'Specified mutation type "{}" not found in document.'.format(
                mutation_type_name
            )
        )

    if subscription_type_name and subscription_type_name not in ast_map:
        raise Exception(
            'Specified subscription type "{}" not found in document.'.format(
                subscription_type_name
            )
        )

    inner_type_map = OrderedDict(
        [
            ("String", GraphQLString),
            ("Int", GraphQLInt),
            ("Float", GraphQLFloat),
            ("Boolean", GraphQLBoolean),
            ("ID", GraphQLID),
            ("__Schema", __Schema),
            ("__Directive", __Directive),
            ("__DirectiveLocation", __DirectiveLocation),
            ("__Type", __Type),
            ("__Field", __Field),
            ("__InputValue", __InputValue),
            ("__EnumValue", __EnumValue),
            ("__TypeKind", __TypeKind),
        ]
    )

    def get_directive(directive_ast):
        return GraphQLDirective(
            name=directive_ast.name.value,
            locations=[node.value for node in directive_ast.locations],
            args=make_input_values(directive_ast.arguments, GraphQLArgument),
        )

    def get_object_type(type_ast):
        type = type_def_named(type_ast.name.value)
        assert isinstance(type, GraphQLObjectType), "AST must provide object type"
        return type

    def produce_type_def(type_ast):
        type_name = _get_named_type_ast(type_ast).name.value
        type_def = type_def_named(type_name)
        return _build_wrapped_type(type_def, type_ast)

    def type_def_named(type_name):
        if type_name in inner_type_map:
            return inner_type_map[type_name]

        if type_name not in ast_map:
            raise Exception('Type "{}" not found in document'.format(type_name))

        inner_type_def = make_schema_def(ast_map[type_name])
        if not inner_type_def:
            raise Exception('Nothing constructed for "{}".'.format(type_name))

        inner_type_map[type_name] = inner_type_def
        return inner_type_def

    def make_schema_def(definition):
        if not definition:
            raise Exception("def must be defined.")

        handler = _schema_def_handlers.get(type(definition))
        if not handler:
            raise Exception(
                'Type kind "{}" not supported.'.format(type(definition).__name__)
            )

        return handler(definition)

    def make_type_def(definition):
        return GraphQLObjectType(
            name=definition.name.value,
            fields=lambda: make_field_def_map(definition),
            interfaces=make_implemented_interfaces(definition),
        )

    def make_field_def_map(definition):
        return OrderedDict(
            (
                f.name.value,
                GraphQLField(
                    type=produce_type_def(f.type),
                    args=make_input_values(f.arguments, GraphQLArgument),
                    deprecation_reason=get_deprecation_reason(f.directives),
                ),
            )
            for f in definition.fields
        )

    def make_implemented_interfaces(definition):
        return [produce_type_def(i) for i in definition.interfaces]

    def make_input_values(values, cls):
        return OrderedDict(
            (
                value.name.value,
                cls(
                    type=produce_type_def(value.type),
                    default_value=value_from_ast(
                        value.default_value, produce_type_def(value.type)
                    ),
                ),
            )
            for value in values
        )

    def make_interface_def(definition):
        return GraphQLInterfaceType(
            name=definition.name.value,
            resolve_type=_none,
            fields=lambda: make_field_def_map(definition),
        )

    def make_enum_def(definition):
        values = OrderedDict(
            (
                v.name.value,
                GraphQLEnumValue(
                    deprecation_reason=get_deprecation_reason(v.directives)
                ),
            )
            for v in definition.values
        )
        return GraphQLEnumType(name=definition.name.value, values=values)

    def make_union_def(definition):
        return GraphQLUnionType(
            name=definition.name.value,
            resolve_type=_none,
            types=[produce_type_def(t) for t in definition.types],
        )

    def make_scalar_def(definition):
        return GraphQLScalarType(
            name=definition.name.value,
            serialize=_none,
            # Validation calls the parse functions to determine if a literal value is correct.
            # Returning none, however would cause the scalar to fail validation. Returning false,
            # will cause them to pass.
            parse_literal=_false,
            parse_value=_false,
        )

    def make_input_object_def(definition):
        return GraphQLInputObjectType(
            name=definition.name.value,
            fields=lambda: make_input_values(
                definition.fields, GraphQLInputObjectField
            ),
        )

    _schema_def_handlers = {
        ast.ObjectTypeDefinition: make_type_def,
        ast.InterfaceTypeDefinition: make_interface_def,
        ast.EnumTypeDefinition: make_enum_def,
        ast.UnionTypeDefinition: make_union_def,
        ast.ScalarTypeDefinition: make_scalar_def,
        ast.InputObjectTypeDefinition: make_input_object_def,
    }
    types = [type_def_named(definition.name.value) for definition in type_defs]
    directives = [get_directive(d) for d in directive_defs]

    # If specified directive were not explicitly declared, add them.
    find_skip_directive = (
        directive.name for directive in directives if directive.name == "skip"
    )
    find_include_directive = (
        directive.name for directive in directives if directive.name == "include"
    )
    find_deprecated_directive = (
        directive.name for directive in directives if directive.name == "deprecated"
    )

    if not next(find_skip_directive, None):
        directives.append(GraphQLSkipDirective)

    if not next(find_include_directive, None):
        directives.append(GraphQLIncludeDirective)

    if not next(find_deprecated_directive, None):
        directives.append(GraphQLDeprecatedDirective)

    schema_kwargs = {"query": get_object_type(ast_map[query_type_name])}

    if mutation_type_name:
        schema_kwargs["mutation"] = get_object_type(ast_map[mutation_type_name])

    if subscription_type_name:
        schema_kwargs["subscription"] = get_object_type(ast_map[subscription_type_name])

    if directive_defs:
        schema_kwargs["directives"] = directives

    if types:
        schema_kwargs["types"] = types

    return GraphQLSchema(**schema_kwargs)


def get_deprecation_reason(directives):
    deprecated_ast = next(
        (
            directive
            for directive in directives
            if directive.name.value == GraphQLDeprecatedDirective.name
        ),
        None,
    )

    if deprecated_ast:
        args = get_argument_values(
            GraphQLDeprecatedDirective.args, deprecated_ast.arguments
        )
        return args["reason"]
    else:
        return None
