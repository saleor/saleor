from typing import Any

from django.conf import settings
from graphql import GraphQLError
from graphql.language.ast import Field
from graphql.validation.rules.base import ValidationRule
from graphql.validation.validation import ValidationContext

from ...metrics import record_graphql_alias_count


class AliasCountLimitRule(ValidationRule):
    """Limits the number of aliases that can be sent within a query."""

    def __init__(self, context: ValidationContext) -> None:
        super().__init__(context)
        self.limit: int = settings.GRAPHQL_ALIAS_COUNT_LIMIT
        self.alias_count_seen: int = 0

    def enter_Field(self, field: Field, *_args: Any) -> None:
        if field.alias is not None:
            self.alias_count_seen += 1

    def leave_Document(self, *_args: Any) -> None:
        if self.alias_count_seen > self.limit:
            self.context.report_error(
                GraphQLError(f"Number of aliases exceed the limit of {self.limit}")
            )
        elif self.alias_count_seen > 0:
            # We only want to record successful requests
            record_graphql_alias_count(self.alias_count_seen)
