from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type, Union, cast

from graphql import (
    GraphQLError,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLSchema,
    get_default_backend,
    get_named_type,
)
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

from ...graphql.api import schema
from .sensitive_data import SENSITIVE_HEADERS, SensitiveFieldsMap

if TYPE_CHECKING:
    from graphql import GraphQLDocument

    from .utils import GraphQLOperationResponse

GraphQLNode = Union[
    Field,
    FragmentDefinition,
    FragmentSpread,
    InlineFragment,
    OperationDefinition,
]
MASK = "***"


def hide_sensitive_headers(
    headers: Dict[str, str], sensitive_headers: Tuple[str, ...] = SENSITIVE_HEADERS
) -> Dict[str, str]:
    return {
        key: val if key.upper().replace("-", "_") not in sensitive_headers else MASK
        for key, val in headers.items()
    }


class SensitiveFieldError(GraphQLError):
    pass


class ContainSensitiveField(ValidationRule):
    def __init__(
        self, sensitive_fields: SensitiveFieldsMap
    ):  # pylint: disable=super-init-not-called
        self.sensitive_fields = sensitive_fields

    def __call__(self, context: ValidationContext):
        self.context = context
        return self

    def is_sensitive_field(self, node: Field, parent_type: str):
        if fields := self.sensitive_fields.get(parent_type):
            node_name = node.name.value
            if node_name in fields:
                raise SensitiveFieldError(
                    "The query contains sensitive field "
                    f"{node_name} of type {parent_type}."
                )

    def contain_sensitive_field(self, node: GraphQLNode, type_def) -> bool:
        if isinstance(node, FragmentSpread) or not node.selection_set:
            return False
        fields: Dict[str, GraphQLField] = {}
        if isinstance(type_def, (GraphQLObjectType, GraphQLInterfaceType)):
            fields = type_def.fields
        for child_node in node.selection_set.selections:
            if isinstance(child_node, Field):
                field = fields.get(child_node.name.value)
                if not field:
                    continue
                field_type = get_named_type(field.type)
                if type_def and type_def.name:
                    self.is_sensitive_field(child_node, type_def.name)
                self.contain_sensitive_field(child_node, field_type)
            if isinstance(child_node, FragmentSpread):
                fragment = self.context.get_fragment(child_node.name.value)
                if fragment:
                    fragment_type = self.context.get_schema().get_type(
                        fragment.type_condition.name.value
                    )
                    self.contain_sensitive_field(fragment, fragment_type)
            if isinstance(child_node, InlineFragment):
                inline_fragment_type = type_def
                if child_node.type_condition and child_node.type_condition.name:
                    inline_fragment_type = self.context.get_schema().get_type(
                        child_node.type_condition.name.value
                    )
                self.contain_sensitive_field(child_node, inline_fragment_type)
        return False

    def enter_operation_definition(
        self, node, key, parent, path, ancestors
    ):  # pylint: disable=unused-argument
        validate_sensitive_fields_map(self.sensitive_fields, self.context.get_schema())
        if node.operation == "query":
            self.contain_sensitive_field(
                node, self.context.get_schema().get_query_type()
            )
        elif node.operation == "mutation":
            self.contain_sensitive_field(
                node, self.context.get_schema().get_mutation_type()
            )
        elif node.operation == "subscription":
            self.contain_sensitive_field(
                node, self.context.get_schema().get_subscription_type()
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


def validate_sensitive_fields_map(
    sensitive_fields: SensitiveFieldsMap, schema: GraphQLSchema
):
    type_map = schema.get_type_map()
    for type_name, type_fields in sensitive_fields.items():
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


def _contain_sensitive_field(
    document: "GraphQLDocument", sensitive_fields: SensitiveFieldsMap
):
    validator = cast(
        Type[ValidationRule], ContainSensitiveField(sensitive_fields=sensitive_fields)
    )
    try:
        validate(document.schema, document.document_ast, [validator])
    except SensitiveFieldError:
        return True
    return False


def anonymize_gql_operation_response(
    operation: "GraphQLOperationResponse", sensitive_fields: SensitiveFieldsMap
):
    if not operation.query or not operation.result:
        return
    if _contain_sensitive_field(operation.query, sensitive_fields):
        operation.result["data"] = MASK


def anonymize_event_payload(
    subscription_query: Optional[str],
    event_type: str,  # pylint: disable=unused-argument
    payload: Any,
    sensitive_fields: SensitiveFieldsMap,
) -> Any:
    if not subscription_query:
        return payload
    graphql_backend = get_default_backend()
    document = graphql_backend.document_from_string(schema, subscription_query)
    if _contain_sensitive_field(document, sensitive_fields):
        return MASK
    return payload
