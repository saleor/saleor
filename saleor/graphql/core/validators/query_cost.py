from functools import reduce
from operator import add, mul
from typing import Any, Dict, List, Optional, Union, cast

from graphql import (
    GraphQLError,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLSchema,
    get_named_type,
)
from graphql.execution.values import get_argument_values
from graphql.language.ast import (
    Field,
    FragmentDefinition,
    FragmentSpread,
    InlineFragment,
    OperationDefinition,
)
from graphql.type import GraphQLField
from graphql.validation import validate
from graphql.validation.rules.base import ValidationRule
from graphql.validation.validation import ValidationContext

CostAwareNode = Union[
    Field,
    FragmentDefinition,
    FragmentSpread,
    InlineFragment,
    OperationDefinition,
]

GraphQLFieldMap = Dict[str, GraphQLField]


class CostValidator(ValidationRule):
    maximum_cost: int
    default_cost: int = 0
    default_complexity: int = 1
    variables: Optional[Dict] = None
    cost_map: Optional[Dict[str, Dict[str, Any]]] = None

    def __init__(
        self,
        maximum_cost: int,
        *,
        default_cost: int = 0,
        default_complexity: int = 1,
        variables: Optional[Dict] = None,
        cost_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ):  # pylint: disable=super-init-not-called
        self.maximum_cost = maximum_cost
        self.variables = variables
        self.cost_map = cost_map
        self.default_cost = default_cost
        self.default_complexity = default_complexity
        self.cost = 0
        self.operation_multipliers: List[Any] = []

    def __call__(self, context: ValidationContext):
        self.context = context
        return self

    def compute_node_cost(self, node: CostAwareNode, type_def, parent_multipliers=None):
        if parent_multipliers is None:
            parent_multipliers = []
        if isinstance(node, FragmentSpread) or not node.selection_set:
            return 0
        fields: GraphQLFieldMap = {}
        if isinstance(type_def, (GraphQLObjectType, GraphQLInterfaceType)):
            fields = type_def.fields
        total = 0
        for child_node in node.selection_set.selections:
            self.operation_multipliers = parent_multipliers[:]
            node_cost = self.default_cost
            if isinstance(child_node, Field):
                field = fields.get(child_node.name.value)
                if not field:
                    continue
                field_type = get_named_type(field.type)
                try:
                    field_args: Dict[str, Any] = get_argument_values(
                        field.args,
                        child_node.arguments,
                        self.variables,
                    )
                except Exception as e:
                    report_error(self.context, e)
                    field_args = {}

                if not self.cost_map:
                    return 0

                cost_map_args = (
                    self.get_args_from_cost_map(child_node, type_def.name, field_args)
                    if type_def and type_def.name
                    else None
                )
                if cost_map_args is not None:
                    try:
                        node_cost = self.compute_cost(**cost_map_args)
                    except (TypeError, ValueError) as e:
                        report_error(self.context, e)

                child_cost = self.compute_node_cost(
                    child_node, field_type, self.operation_multipliers
                )
                node_cost += child_cost
            if isinstance(child_node, FragmentSpread):
                fragment = self.context.get_fragment(child_node.name.value)
                if fragment:
                    fragment_type = self.context.get_schema().get_type(
                        fragment.type_condition.name.value
                    )
                    node_cost = self.compute_node_cost(fragment, fragment_type)
            if isinstance(child_node, InlineFragment):
                inline_fragment_type = type_def
                if child_node.type_condition and child_node.type_condition.name:
                    inline_fragment_type = self.context.get_schema().get_type(
                        child_node.type_condition.name.value
                    )
                node_cost = self.compute_node_cost(child_node, inline_fragment_type)
            total += node_cost
        return total

    def enter_operation_definition(
        self, node, key, parent, path, ancestors
    ):  # pylint: disable=unused-argument
        if self.cost_map:
            try:
                validate_cost_map(self.cost_map, self.context.get_schema())
            except GraphQLError as cost_map_error:
                self.context.report_error(cost_map_error)
                return

        if node.operation == "query":
            self.cost += self.compute_node_cost(
                node, self.context.get_schema().get_query_type()
            )
        if node.operation == "mutation":
            self.cost += self.compute_node_cost(
                node, self.context.get_schema().get_mutation_type()
            )
        if node.operation == "subscription":
            self.cost += self.compute_node_cost(
                node, self.context.get_schema().get_subscription_type()
            )

    def leave_operation_definition(
        self, node, key, parent, path, ancestors
    ):  # pylint: disable=unused-argument
        if self.cost > self.maximum_cost:
            self.context.report_error(self.get_cost_exceeded_error())

    def compute_cost(self, multipliers=None, use_multipliers=True, complexity=None):
        if complexity is None:
            complexity = self.default_complexity
        if use_multipliers:
            if multipliers:
                multiplier = reduce(add, multipliers, 0)
                self.operation_multipliers = self.operation_multipliers + [multiplier]
            return reduce(mul, self.operation_multipliers, complexity)
        return complexity

    def get_args_from_cost_map(self, node: Field, parent_type: str, field_args: Dict):
        cost_args = None
        cost_map = cast(Dict[Any, Dict], self.cost_map)
        if parent_type in cost_map:
            cost_args = cost_map[parent_type].get(node.name.value)
        if not cost_args:
            return None
        cost_args = cost_args.copy()
        if "multipliers" in cost_args:
            cost_args["multipliers"] = self.get_multipliers_from_string(
                cost_args["multipliers"], field_args
            )
        return cost_args

    def get_multipliers_from_string(self, multipliers: List[str], field_args):
        accessors = [s.split(".") for s in multipliers]
        multipliers: Any = []
        for accessor in accessors:
            val = field_args
            for key in accessor:
                val = val.get(key)
            try:
                multipliers.append(int(val))
            except (ValueError, TypeError):
                pass
        multipliers = [
            len(multiplier) if isinstance(multiplier, (list, tuple)) else multiplier
            for multiplier in multipliers
        ]
        return [m for m in multipliers if m > 0]

    def get_cost_exceeded_error(self) -> "QueryCostError":
        return QueryCostError(
            cost_analysis_message(self.maximum_cost, self.cost),
            extensions={
                "cost": {
                    "requestedQueryCost": self.cost,
                    "maximumAvailable": self.maximum_cost,
                }
            },
        )

    def enter(
        self,
        node: Any,
        key: Optional[Union[int, str]],
        parent: Any,
        path: List[Union[int, str]],
        ancestors: List[Any],
    ):
        if isinstance(node, OperationDefinition):
            self.enter_operation_definition(node, key, parent, path, ancestors)

    def leave(
        self,
        node: Any,
        key: Optional[Union[int, str]],
        parent: Any,
        path: List[Union[int, str]],
        ancestors: List[Any],
    ):
        if isinstance(node, OperationDefinition):
            self.leave_operation_definition(node, key, parent, path, ancestors)


def validate_cost_map(cost_map: Dict[str, Dict[str, Any]], schema: GraphQLSchema):
    type_map = schema.get_type_map()
    for type_name, type_fields in cost_map.items():
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


def report_error(context: ValidationContext, error: Exception):
    context.report_error(GraphQLError(str(error)))


def cost_analysis_message(maximum_cost: int, cost: int) -> str:
    return (
        f"The query exceeds the maximum cost of {maximum_cost}. Actual cost is {cost}"
    )


class QueryCostError(GraphQLError):
    pass


def cost_validator(
    maximum_cost: int,
    *,
    default_cost: int = 0,
    default_complexity: int = 1,
    variables: Optional[Dict] = None,
    cost_map: Optional[Dict[str, Dict[str, Any]]] = None,
) -> CostValidator:
    return CostValidator(
        maximum_cost=maximum_cost,
        default_cost=default_cost,
        default_complexity=default_complexity,
        variables=variables,
        cost_map=cost_map,
    )


def validate_query_cost(
    schema,
    query,
    variables,
    cost_map,
    maximum_cost,
):
    validator = cost_validator(
        maximum_cost,
        variables=variables,
        cost_map=cost_map,
    )
    error = validate(
        schema,
        query.document_ast,
        [validator],  # type: ignore[list-item] # cost validator is an instance that pretends to be a class # noqa: E501
    )
    if error:
        return validator.cost, error
    return validator.cost, None
