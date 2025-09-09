from functools import reduce
from operator import add, mul
from typing import Any, cast

from graphql import (
    DocumentNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLError,
    GraphQLField,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLSchema,
    InlineFragmentNode,
    OperationDefinitionNode,
    OperationType,
    get_argument_values,
    get_named_type,
)

from ...query_cost_map import COST_MAP

CostAwareNode = (
    FieldNode
    | FragmentDefinitionNode
    | FragmentSpreadNode
    | InlineFragmentNode
    | OperationDefinitionNode
)

GraphQLFieldMap = dict[str, GraphQLField]


def find_query_fragment(
    query: DocumentNode, name: str
) -> FragmentDefinitionNode | None:
    for definition in query.definitions:
        if (
            isinstance(definition, FragmentDefinitionNode)
            and definition.name.value == name
        ):
            return definition
    return None


def get_multipliers_from_string(multipliers: list[str], field_args) -> list[int]:
    accessors = [s.split(".") for s in multipliers]
    results: list[int] = []
    for accessor in accessors:
        val = field_args
        for key in accessor:
            val = val.get(key)
        try:
            results.append(int(val))
        except (ValueError, TypeError):
            pass
    results = [
        len(multiplier) if isinstance(multiplier, list | tuple) else multiplier
        for multiplier in results
    ]
    return [m for m in results if m > 0]


def get_args_from_cost_map(node: FieldNode, parent_type: str, field_args: dict):
    cost_args = None
    if parent_type in COST_MAP:
        cost_args = COST_MAP[parent_type].get(node.name.value)
    if not cost_args:
        return None
    cost_args = cost_args.copy()
    if "multipliers" in cost_args:
        cost_args["multipliers"] = get_multipliers_from_string(
            cost_args["multipliers"], field_args
        )
    return cost_args


def calculate_cost_of_node(
    node: CostAwareNode,
    query: DocumentNode,
    schema: GraphQLSchema,
    variables: dict,
    type_def: GraphQLObjectType,
    parent_multipliers=None,
):
    if parent_multipliers is None:
        parent_multipliers = []
    if isinstance(node, FragmentSpreadNode) or not node.selection_set:
        return 0
    fields: GraphQLFieldMap = {}
    if isinstance(type_def, GraphQLObjectType | GraphQLInterfaceType):
        fields = type_def.fields
    total = 0
    for child_node in node.selection_set.selections:
        operation_multipliers = parent_multipliers[:]
        node_cost = 0
        if isinstance(child_node, FieldNode):
            field = fields.get(child_node.name.value)
            if not field:
                continue
            field_type = cast(GraphQLObjectType, get_named_type(field.type))
            try:
                field_args: dict[str, Any] = get_argument_values(
                    field,
                    child_node,
                    variables,
                )
            except Exception:
                field_args = {}

            cost_map_args = (
                get_args_from_cost_map(child_node, type_def.name, field_args)
                if type_def and type_def.name
                else None
            )
            if cost_map_args is not None:
                complexity = cost_map_args.get("complexity", 1)
                multipliers = cost_map_args.get("multipliers", [])
                if multipliers:
                    multiplier = reduce(add, multipliers, 0)
                    operation_multipliers += [multiplier]
                node_cost = reduce(mul, operation_multipliers, complexity)

            child_cost = calculate_cost_of_node(
                child_node, query, schema, variables, field_type, operation_multipliers
            )
            node_cost += child_cost
        if isinstance(child_node, FragmentSpreadNode):
            fragment = find_query_fragment(query, child_node.name.value)
            if fragment:
                fragment_type = cast(
                    GraphQLObjectType,
                    schema.get_type(fragment.type_condition.name.value),
                )
                node_cost = calculate_cost_of_node(
                    fragment,
                    query,
                    schema,
                    variables,
                    fragment_type,
                    operation_multipliers,
                )
        if isinstance(child_node, InlineFragmentNode):
            inline_fragment_type = type_def
            if child_node.type_condition and child_node.type_condition.name:
                inline_fragment_type = cast(
                    GraphQLObjectType,
                    schema.get_type(child_node.type_condition.name.value),
                )
            node_cost = calculate_cost_of_node(
                child_node,
                query,
                schema,
                variables,
                inline_fragment_type,
                operation_multipliers,
            )
        total += node_cost
    return total


def calculate_cost_of_operation(
    node: OperationDefinitionNode,
    query: DocumentNode,
    schema: GraphQLSchema,
    variables: dict,
) -> int:
    if node.operation == OperationType.QUERY:
        return calculate_cost_of_node(
            node,
            query,
            schema,
            variables,
            cast(GraphQLObjectType, schema.query_type),
        )
    if node.operation == OperationType.MUTATION:
        return calculate_cost_of_node(
            node,
            query,
            schema,
            variables,
            cast(GraphQLObjectType, schema.mutation_type),
        )
    if node.operation == OperationType.SUBSCRIPTION:
        return calculate_cost_of_node(
            node,
            query,
            schema,
            variables,
            cast(GraphQLObjectType, schema.subscription_type),
        )
    raise GraphQLError(
        f"Unknown operation type: {node.operation}",
    )


def calculate_cost_of_query(
    query: DocumentNode, schema: GraphQLSchema, variables: dict
) -> int:
    validate_cost_map(schema)

    total = 0
    for definition in query.definitions:
        if isinstance(definition, OperationDefinitionNode):
            total += calculate_cost_of_operation(definition, query, schema, variables)
    return total


def validate_cost_map(schema: GraphQLSchema):
    type_map = schema.type_map
    for type_name, type_fields in COST_MAP.items():
        if type_name not in type_map:
            raise GraphQLError(
                "The query cost could not be calculated because cost map specifies "
                f"a type {type_name} that is not defined by the schema."
            )

        if not isinstance(type_map[type_name], GraphQLObjectType):
            raise GraphQLError(
                "The query cost could not be calculated because cost map specifies "
                f"a type {type_name} that is defined by the schema, but is not an "
                "object type."
            )

        for field_name in type_fields:
            graphql_type = cast(GraphQLObjectType, type_map[type_name])
            if field_name not in graphql_type.fields:
                raise GraphQLError(
                    "The query cost could not be calculated because cost map contains "
                    f"a field {field_name} not defined by the {type_name} type."
                )
