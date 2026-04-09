from typing import Any

from django.conf import settings
from graphql import GraphQLError
from graphql.language.ast import OperationDefinition
from graphql.validation.rules.base import ValidationRule
from graphql.validation.validation import ValidationContext

from ...metrics import record_graphql_mutation_count


class MutationCountLimitRule(ValidationRule):
    """Limits the number of mutations within a single request."""

    def __init__(self, context: ValidationContext) -> None:
        super().__init__(context)
        self.limit: int = settings.GRAPHQL_MUTATION_COUNT_LIMIT
        self.seen_count: int = 0

    def enter_OperationDefinition(self, node: OperationDefinition, *_args: Any) -> None:
        if node.operation == "mutation" and node.selection_set:
            self.seen_count += len(node.selection_set.selections)

    def leave_Document(self, *_args: Any) -> None:
        if self.seen_count > self.limit:
            self.context.report_error(
                GraphQLError(f"Number of mutations exceed the limit of {self.limit}")
            )
        # We only want to record successful requests & requests that use more than 1
        # mutation
        elif self.seen_count > 1:
            record_graphql_mutation_count(self.seen_count)
