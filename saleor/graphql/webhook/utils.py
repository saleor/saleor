from enum import Enum, Flag
from typing import Dict, List, Optional, Union

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


class IsFragment(Flag):
    TRUE = True
    FALSE = False


class SubscriptionQueryErrorCode(Enum):
    MISSING_SUBSCRIPTION = "Subscription operation can't be found."
    MISSING_EVENT_FIELD = "Event field can't be found."
    MISSING_EVENTS = "Can't find a single event."


class SubscriptionQuery:
    def __init__(self, query: str):
        self.query: str = query
        self.is_valid: bool = False
        self.ast: Optional[Document] = None
        self.events: List[str] = []
        self.errors = self.validate_query()

    def validate_query(self):
        from ..api import schema

        graphql_backend = get_default_backend()
        try:
            document = graphql_backend.document_from_string(schema, self.query)
            self.ast = document.document_ast
            errors = validate(schema, self.ast)
        except GraphQLSyntaxError as e:
            return [e]

        if errors:
            return errors

        try:
            self.events = self.get_events_from_subscription()
        except Exception as err:
            return [err]

        self.is_valid = not bool(errors)
        return []

    def get_events_from_subscription(self) -> List[str]:
        subscription = self._get_subscription(self.ast)
        if not subscription:
            err = SubscriptionQueryErrorCode.MISSING_SUBSCRIPTION
            raise ValidationError(err.value)

        event_type = self._get_event_type_from_subscription(subscription)
        if not event_type:
            err = SubscriptionQueryErrorCode.MISSING_EVENT_FIELD
            raise ValidationError(err.value)

        events_and_fragments: Dict[str, IsFragment] = self._get_events_from_field(
            event_type
        )
        if not events_and_fragments:
            err = SubscriptionQueryErrorCode.MISSING_EVENTS
            raise ValidationError(err.value)

        fragment_definitions = self._get_fragment_definitions(self.ast)
        unpacked_events: Dict[str, IsFragment] = {}
        for event_name, is_fragment in events_and_fragments.items():
            if not is_fragment:
                continue
            event_definition = fragment_definitions[event_name]
            unpacked_events.update(self._get_events_from_field(event_definition))
        events_and_fragments.update(unpacked_events)

        events = [k for k, v in events_and_fragments.items() if not v]
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
    def _get_event_type_from_subscription(
        subscription: OperationDefinition,
    ) -> Optional[Field]:
        for field in subscription.selection_set.selections:
            if field.name.value == "event" and isinstance(field, Field):
                return field
        return None

    @staticmethod
    def _get_events_from_field(
        field: Union[Field, FragmentDefinition]
    ) -> Dict[str, IsFragment]:
        events: Dict[str, IsFragment] = {}
        if field.selection_set:
            for field in field.selection_set.selections:
                if isinstance(field, InlineFragment) and field.type_condition:
                    events[field.type_condition.name.value] = IsFragment.FALSE
                if isinstance(field, FragmentSpread):
                    events[field.name.value] = IsFragment.TRUE
            return events
        return events

    @staticmethod
    def _get_fragment_definitions(ast: Document) -> Dict[str, FragmentDefinition]:
        fragments: Dict[str, FragmentDefinition] = {}
        for definition in ast.definitions:
            if isinstance(definition, FragmentDefinition):
                fragments[definition.name.value] = definition
        return fragments
