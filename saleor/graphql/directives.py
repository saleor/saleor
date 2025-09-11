from typing import Any

import graphql
from graphene_directives import DirectiveLocation, directive
from graphene_federation import ComposableDirective

DocDirective = ComposableDirective(
    name="doc",
    description="Groups fields and types into named documentation categories.",
    args={
        "category": graphql.GraphQLArgument(
            type_=graphql.GraphQLNonNull(graphql.GraphQLString),
            description="Name of the documentation category",
        )
    },
    locations=[
        DirectiveLocation.ENUM,
        DirectiveLocation.FIELD_DEFINITION,
        DirectiveLocation.INPUT_FIELD_DEFINITION,
        DirectiveLocation.INPUT_OBJECT,
        DirectiveLocation.INTERFACE,
        DirectiveLocation.OBJECT,
        DirectiveLocation.UNION,
    ],
    add_to_schema_directives=False,
)


def doc(category: str, field: Any | None = None):
    return directive(target_directive=DocDirective, category=category, field=field)


WebhookEventsDirective = ComposableDirective(
    name="webhookEventsInfo",
    description="Webhook events triggered by a specific location.",
    args={
        "asyncEvents": graphql.GraphQLArgument(
            graphql.GraphQLList(graphql.GraphQLNonNull(graphql.GraphQLString)),
            description=(
                "List of asynchronous webhook events triggered by a specific location."
            ),
        ),
        "syncEvents": graphql.GraphQLArgument(
            graphql.GraphQLList(graphql.GraphQLNonNull(graphql.GraphQLString)),
            description=(
                "List of synchronous webhook events triggered by a specific location."
            ),
        ),
    },
    locations=[
        DirectiveLocation.FIELD_DEFINITION,
        DirectiveLocation.OBJECT,
    ],
    add_to_schema_directives=False,
)


def webhook_events(
    async_events: set[str] | None = None,
    sync_events: set[str] | None = None,
    field: Any | None = None,
):
    from ..webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType

    assert async_events or sync_events, "Must provide at least one event type"
    if async_events:
        assert all(e in WebhookEventAsyncType.ALL for e in async_events)
        async_event_list = [e.upper() for e in sorted(async_events)]
    else:
        async_event_list = None
    if sync_events:
        assert all(e in WebhookEventSyncType.ALL for e in sync_events)
        sync_event_list = [e.upper() for e in sorted(sync_events)]
    else:
        sync_event_list = None
    return directive(
        target_directive=WebhookEventsDirective,
        async_events=async_event_list,
        sync_events=sync_event_list,
        field=field,
    )
