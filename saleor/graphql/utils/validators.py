from django.core.exceptions import ValidationError
from graphql import GraphQLDocument
from graphql.error import GraphQLError
from graphql.language.ast import (
    Field,
    FragmentDefinition,
    InlineFragment,
    OperationDefinition,
)

from ..core.utils import get_duplicates_items


def check_for_duplicates(
    input_data: dict, add_field: str, remove_field: str, error_class_field: str
):
    """Check if any items are on both input field.

    Raise error if some of items are duplicated.
    """
    error = None
    duplicated_items = get_duplicates_items(
        input_data.get(add_field), input_data.get(remove_field)
    )
    if duplicated_items:
        # add error
        error_msg = (
            "The same object cannot be in both list for adding and removing items."
        )
        params = {error_class_field: list(duplicated_items)}
        error = ValidationError(message=error_msg, params=params)

    return error


def __queries_or_introspection_in_selections(selections: list, is_query: bool):
    found_queries = False
    found_introspection = False
    for selection in selections:
        if isinstance(selection, Field):
            selection_name = str(selection.name.value)
            if is_query and selection_name == "__schema":
                found_introspection = True
            else:
                found_queries = True
        if isinstance(selection, InlineFragment):
            (
                sub_queries,
                sub_introspection,
            ) = __queries_or_introspection_in_inline_fragment(
                selection, is_query=is_query
            )
            found_queries = found_queries or sub_queries
            found_introspection = found_introspection or sub_introspection
    return found_queries, found_introspection


def __queries_or_introspection_in_inline_fragment(
    fragment: InlineFragment, is_query: bool
):
    if fragment.type_condition and fragment.type_condition.name.value == "__Schema":
        return False, True
    selections = fragment.selection_set.selections
    if (fragment.type_condition and fragment.type_condition.name.value == "Query") or (
        is_query and not fragment.type_condition
    ):
        return __queries_or_introspection_in_selections(selections, is_query=True)
    else:
        return __queries_or_introspection_in_selections(selections, is_query=False)


def __queries_or_introspection_in_operation_definition(definition: OperationDefinition):
    if definition.operation != "query":
        return False, False
    selections = definition.selection_set.selections
    return __queries_or_introspection_in_selections(selections, is_query=True)


def __queries_or_introspection_in_fragment_definition(definition: FragmentDefinition):
    selections = definition.selection_set.selections
    if definition.type_condition:
        if definition.type_condition.name.value == "Query":
            return __queries_or_introspection_in_selections(selections, is_query=True)
        if definition.type_condition.name.value.startswith("__"):
            return False, True
    return __queries_or_introspection_in_selections(selections, is_query=False)


def check_if_query_contains_only_schema(document: GraphQLDocument):
    found_queries = False
    found_introspection = False
    for definition in document.document_ast.definitions:
        if isinstance(definition, OperationDefinition):
            (
                sub_queries,
                sub_introspection,
            ) = __queries_or_introspection_in_operation_definition(definition)
            found_queries = found_queries or sub_queries
            found_introspection = found_introspection or sub_introspection
        if isinstance(definition, FragmentDefinition):
            (
                sub_queries,
                sub_introspection,
            ) = __queries_or_introspection_in_fragment_definition(definition)
            found_queries = found_queries or sub_queries
            found_introspection = found_introspection or sub_introspection
    if found_introspection and found_queries:
        raise GraphQLError(
            "Queries and introspection cannot be mixed in the same request."
        )
    return found_introspection
