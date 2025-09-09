from typing import TYPE_CHECKING, Any, cast

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
    ValidationContext,
    ValidationRule,
    get_named_type,
    parse,
    validate,
)

from .sensitive_data import ALLOWED_HEADERS, SENSITIVE_GQL_FIELDS, SENSITIVE_HEADERS

if TYPE_CHECKING:
    from .utils import GraphQLOperationResponse

GraphQLNode = (
    FieldNode
    | FragmentDefinitionNode
    | FragmentSpreadNode
    | InlineFragmentNode
    | OperationDefinitionNode
)
MASK = "***"


def filter_and_hide_headers(
    headers: dict[str, str],
    allowed=ALLOWED_HEADERS,
    sensitive=SENSITIVE_HEADERS,
) -> dict[str, str]:
    filtered_headers = {}
    for key, val in headers.items():
        lowered = key.lower()
        if lowered in allowed:
            if lowered in sensitive:
                filtered_headers[key] = MASK
            else:
                filtered_headers[key] = val
    return filtered_headers


class SensitiveFieldError(GraphQLError):
    pass


class ContainSensitiveField(ValidationRule):
    def __call__(self, context: ValidationContext):
        self.context = context
        return self

    def is_sensitive_field(self, node: FieldNode, parent_type: str):
        if fields := SENSITIVE_GQL_FIELDS.get(parent_type):
            node_name = node.name.value
            if node_name in fields:
                raise SensitiveFieldError(
                    "The query contains sensitive field "
                    f"{node_name} of type {parent_type}."
                )

    def contain_sensitive_field(self, node: GraphQLNode, type_def) -> bool:
        if isinstance(node, FragmentSpreadNode) or not node.selection_set:
            return False
        fields: dict[str, GraphQLField] = {}
        if isinstance(type_def, GraphQLObjectType | GraphQLInterfaceType):
            fields = type_def.fields
        for child_node in node.selection_set.selections:
            if isinstance(child_node, FieldNode):
                field = fields.get(child_node.name.value)
                if not field:
                    continue
                field_type = get_named_type(field.type)
                if type_def and type_def.name:
                    self.is_sensitive_field(child_node, type_def.name)
                self.contain_sensitive_field(child_node, field_type)
            if isinstance(child_node, FragmentSpreadNode):
                fragment = self.context.get_fragment(child_node.name.value)
                if fragment:
                    fragment_type = self.context.schema.get_type(
                        fragment.type_condition.name.value
                    )
                    self.contain_sensitive_field(fragment, fragment_type)
            if isinstance(child_node, InlineFragmentNode):
                inline_fragment_type = type_def
                if child_node.type_condition and child_node.type_condition.name:
                    inline_fragment_type = self.context.schema.get_type(
                        child_node.type_condition.name.value
                    )
                self.contain_sensitive_field(child_node, inline_fragment_type)
        return False

    def enter_operation_definition(self, node, key, parent, path, ancestors):  # pylint: disable=unused-argument
        validate_sensitive_fields_map(self.context.schema)
        if node.operation.name == "QUERY":
            self.contain_sensitive_field(node, self.context.schema.query_type)
        elif node.operation.name == "MUTATION":
            self.contain_sensitive_field(node, self.context.schema.mutation_type)
        elif node.operation.name == "SUBSCRIPTION":
            self.contain_sensitive_field(node, self.context.schema.subscription_type)

    def enter(
        self,
        node: Any,
        key: int | str | None,
        parent: Any,
        path: list[int | str],
        ancestors: list[Any],
    ):
        if isinstance(node, OperationDefinitionNode):
            self.enter_operation_definition(node, key, parent, path, ancestors)


def validate_sensitive_fields_map(schema: GraphQLSchema):
    type_map = schema.type_map
    for type_name, type_fields in SENSITIVE_GQL_FIELDS.items():
        if type_name not in type_map:
            raise GraphQLError(
                "The query anonymization could not be performed "
                f"because a type {type_name} that is not defined "
                "is specified as sensitive."
            )
        if not isinstance(type_map[type_name], GraphQLObjectType):
            raise GraphQLError(
                "The query anonymization could not be performed because a type "
                f"{type_name} specified as sensitive is not an object type."
            )
        for field_name in type_fields:
            graphql_type = cast(GraphQLObjectType, type_map[type_name])
            if field_name not in graphql_type.fields:
                raise GraphQLError(
                    "The query anonymization could not be performed because a field "
                    f"{field_name} specified as sensitive is not "
                    f"defined by the {type_name} type."
                )


def _contain_sensitive_field(document: DocumentNode):
    from ...graphql.api import schema

    if not document:
        return False

    try:
        validate(
            schema.graphql_schema,
            document,
            [ContainSensitiveField],
        )
    except SensitiveFieldError:
        return True
    return False


def anonymize_gql_operation_response(operation: "GraphQLOperationResponse"):
    if not operation.query or not operation.result:
        return
    if _contain_sensitive_field(operation.query):
        operation.result["data"] = MASK


def anonymize_event_payload(
    subscription_query: str | None,
    event_type: str,  # pylint: disable=unused-argument
    payload: Any,
) -> Any:
    if not subscription_query:
        return payload

    document = parse(subscription_query)
    if _contain_sensitive_field(document):
        return MASK
    return payload
