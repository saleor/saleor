from enum import Flag
from typing import Optional, Union

from django.core.exceptions import ValidationError
from graphene.utils.str_converters import to_snake_case
from graphql import get_default_backend, validate
from graphql.error import GraphQLSyntaxError
from graphql.language.ast import (
    Document,
    Field,
    FragmentDefinition,
    FragmentSpread,
    InlineFragment,
    OperationDefinition,
)

from ...webhook.error_codes import WebhookErrorCode


class IsFragment(Flag):
    TRUE = True
    FALSE = False


class SubscriptionQuery:
    def __init__(self, query: str):
        self.query: str = query
        self.is_valid: bool = False
        self.ast: Document = Document("")
        self.events: list[str] = []
        self.error_code: Optional[str] = None
        self.errors = self.validate_query()
        self.error_msg: str = ";".join(set([str(err.message) for err in self.errors]))

    def validate_query(self) -> list[Union[GraphQLSyntaxError, ValidationError]]:
        from ..api import schema

        graphql_backend = get_default_backend()
        try:
            document = graphql_backend.document_from_string(schema, self.query)
            self.ast = document.document_ast
            errors = validate(schema, self.ast)
        except GraphQLSyntaxError as e:
            self.error_code = WebhookErrorCode.SYNTAX.value
            return [e]

        if errors:
            self.error_code = WebhookErrorCode.GRAPHQL_ERROR.value
            return errors

        try:
            self.events = self.get_events_from_subscription()
        except ValidationError as err:
            self.error_code = err.code
            return [err]

        self.is_valid = True
        return []

    def get_events_from_subscription(self) -> list[str]:
        subscription = self._get_subscription(self.ast)
        if not subscription:
            raise ValidationError(
                message="Subscription operation can't be found.",
                code=WebhookErrorCode.MISSING_SUBSCRIPTION.value,
            )

        event_types = self._get_event_types_from_subscription(subscription)
        if not event_types:
            raise ValidationError(
                message="Event field can't be found.",
                code=WebhookErrorCode.UNABLE_TO_PARSE.value,
            )

        events_and_fragments: dict[str, IsFragment] = {}
        for event_type in event_types:
            self._get_events_from_field(event_type, events_and_fragments)

        fragment_definitions = self._get_fragment_definitions(self.ast)
        unpacked_events: dict[str, IsFragment] = {}
        for event_name, is_fragment in events_and_fragments.items():
            if not is_fragment:
                continue
            event_definition = fragment_definitions[event_name]
            self._get_events_from_field(event_definition, unpacked_events)
        events_and_fragments.update(unpacked_events)
        events = [k for k, v in events_and_fragments.items() if not v]

        if not events:
            raise ValidationError(
                message="Can't find a single event.",
                code=WebhookErrorCode.MISSING_EVENT.value,
            )

        return sorted(list(map(to_snake_case, events)))

    @staticmethod
    def _get_subscription(ast: Document) -> Optional[OperationDefinition]:
        for definition in ast.definitions:
            if (
                hasattr(definition, "operation")
                and definition.operation == "subscription"
            ):
                return definition
        return None

    @staticmethod
    def _get_event_types_from_subscription(
        subscription: OperationDefinition,
    ) -> list[Field]:
        return [
            field
            for field in subscription.selection_set.selections
            if field.name.value == "event" and isinstance(field, Field)
        ]

    @staticmethod
    def _get_events_from_field(
        field: Union[Field, FragmentDefinition],
        events: dict[str, IsFragment],
    ) -> dict[str, IsFragment]:
        if (
            isinstance(field, FragmentDefinition)
            and field.type_condition
            and field.type_condition.name.value != "Event"
        ):
            events[field.type_condition.name.value] = IsFragment.FALSE
            return events

        if field.selection_set:
            for f in field.selection_set.selections:
                if isinstance(f, InlineFragment) and f.type_condition:
                    events[f.type_condition.name.value] = IsFragment.FALSE
                if isinstance(f, FragmentSpread):
                    events[f.name.value] = IsFragment.TRUE
            return events

        return events

    @staticmethod
    def _get_fragment_definitions(ast: Document) -> dict[str, FragmentDefinition]:
        fragments: dict[str, FragmentDefinition] = {}
        for definition in ast.definitions:
            if isinstance(definition, FragmentDefinition):
                fragments[definition.name.value] = definition
        return fragments
