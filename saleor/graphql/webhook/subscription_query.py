from enum import Flag
from typing import cast

from django.core.exceptions import ValidationError
from graphene.utils.str_converters import to_snake_case
from graphql import (
    DocumentNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLError,
    GraphQLSyntaxError,
    InlineFragmentNode,
    OperationDefinitionNode,
    parse,
    validate,
)

from ...webhook.error_codes import WebhookErrorCode


class IsFragment(Flag):
    TRUE = True
    FALSE = False


class SubscriptionQuery:
    def __init__(self, query: str):
        self.query: str = query
        self.is_valid: bool = False
        self.ast: DocumentNode = DocumentNode()
        self.events: list[str] = []
        self.error_code: str | None = None
        self.errors = self.validate_query()
        self.error_msg: str = ";".join({str(err.message) for err in self.errors})

    def get_filterable_channel_slugs(self) -> list[str]:
        """Get filterable channel slugs from the subscription.

        Subscription is filterable if it has arguments provided that can be used to
        filter out records. If arguments are not provided, the subscription is not
        filterable, then needs to be treated as normal subscription.
        """
        if not self.is_valid:
            return []
        subscription = self._get_subscription(self.ast)
        # subscription is not optional as validation from init already passed
        subscription = cast(OperationDefinitionNode, subscription)

        field_names = [
            selection.name.value
            for selection in subscription.selection_set.selections
            if isinstance(selection, FieldNode | FragmentSpreadNode)
        ]
        # Skip if there is non-filterable subscription
        if len(field_names) > 1 or set(field_names) == {"event"}:
            return []

        selection = subscription.selection_set.selections[0]
        if isinstance(selection, FieldNode):
            if not selection.arguments:
                return []
            channels = []
            for arg in selection.arguments:
                argument_name = arg.name.value
                argument_values = getattr(arg.value, "values", [])
                if argument_name == "channels":
                    channels = [value.value for value in argument_values]
                    break
            return channels
        return []

    def _check_if_invalid_top_field_selection(
        self, subscription: OperationDefinitionNode
    ):
        """Check if subscription selects only one top field.

        Filterable subscription can select only one top field. If more than one field
        is selected, the subscription is invalid.
        """
        is_invalid = False
        field_names = [
            selection.name.value
            for selection in subscription.selection_set.selections
            if isinstance(selection, FieldNode | FragmentSpreadNode)
        ]
        if len(field_names) > 1 and set(field_names) != {"event"}:
            is_invalid = True
        return is_invalid

    def validate_query(self) -> list[GraphQLError]:
        from ..api import schema

        try:
            document = parse(self.query)
            self.ast = document
            errors = validate(schema.graphql_schema, self.ast)
        except GraphQLSyntaxError as e:
            self.error_code = WebhookErrorCode.SYNTAX.value
            return [e]

        if errors:
            self.error_code = WebhookErrorCode.GRAPHQL_ERROR.value
            return errors

        subscription = self._get_subscription(self.ast)
        if not subscription:
            self.error_code = WebhookErrorCode.MISSING_SUBSCRIPTION.value
            return [
                GraphQLError(
                    "Subscription operation can't be found.",
                    extensions={"code": WebhookErrorCode.MISSING_SUBSCRIPTION.value},
                )
            ]

        if self._check_if_invalid_top_field_selection(subscription):
            self.error_code = WebhookErrorCode.INVALID.value
            return [
                GraphQLError(
                    "Subscription must select only one top field.",
                    extensions={"code": WebhookErrorCode.INVALID.value},
                )
            ]

        try:
            self.events = self.get_events_from_subscription(subscription)
        except ValidationError as err:
            self.error_code = err.code
            return [GraphQLError(str(err), extensions={"code": err.code})]

        self.is_valid = True
        return []

    def get_events_from_subscription(self, subscription) -> list[str]:
        subscription_name = subscription.selection_set.selections[0].name.value
        if subscription_name != "event":
            return [
                to_snake_case(selection.name.value)
                for selection in subscription.selection_set.selections
            ]

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

        return sorted(map(to_snake_case, events))

    @staticmethod
    def _get_subscription(ast: DocumentNode) -> OperationDefinitionNode | None:
        for definition in ast.definitions:
            if (
                isinstance(definition, OperationDefinitionNode)
                and definition.operation == "subscription"
            ):
                return definition
        return None

    @staticmethod
    def _get_event_types_from_subscription(
        subscription: OperationDefinitionNode,
    ) -> list[FieldNode]:
        return [
            field
            for field in subscription.selection_set.selections
            if isinstance(field, FieldNode) and field.name.value == "event"
        ]

    @staticmethod
    def _get_events_from_field(
        field: FieldNode | FragmentDefinitionNode,
        events: dict[str, IsFragment],
    ) -> dict[str, IsFragment]:
        if (
            isinstance(field, FragmentDefinitionNode)
            and field.type_condition
            and field.type_condition.name.value != "Event"
        ):
            events[field.type_condition.name.value] = IsFragment.FALSE
            return events

        if field.selection_set:
            for f in field.selection_set.selections:
                if isinstance(f, InlineFragmentNode) and f.type_condition:
                    events[f.type_condition.name.value] = IsFragment.FALSE
                if isinstance(f, FragmentSpreadNode):
                    events[f.name.value] = IsFragment.TRUE
            return events

        return events

    @staticmethod
    def _get_fragment_definitions(
        ast: DocumentNode,
    ) -> dict[str, FragmentDefinitionNode]:
        fragments: dict[str, FragmentDefinitionNode] = {}
        for definition in ast.definitions:
            if isinstance(definition, FragmentDefinitionNode):
                fragments[definition.name.value] = definition
        return fragments
