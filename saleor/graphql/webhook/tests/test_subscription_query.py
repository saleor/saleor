import pytest
from django.core.exceptions import ValidationError
from graphql import GraphQLError
from graphql.error import GraphQLSyntaxError

from saleor.webhook.error_codes import WebhookErrorCode

from ..subscription_query import IsFragment, SubscriptionQuery


def test_subscription_query():
    # given
    query = """
        fragment EventFragment on Event {
          ... on OrderUpdated {
            order {
                id
            }
          }
          ... on OrderCreated {
            order {
                id
            }
          }
        }

        subscription {
          event {
            ... EventFragment
            ... on ProductCreated {
                product {
                    id
                }
            }
          }
        }
    """

    # when
    subscription_query = SubscriptionQuery(query)

    # then
    assert subscription_query.is_valid
    assert subscription_query.ast
    assert not subscription_query.errors
    assert subscription_query.events == [
        "order_created",
        "order_updated",
        "product_created",
    ]


@pytest.mark.parametrize(
    ("query", "events"),
    [
        (
            """
            subscription {
              event {
                ...on OrderCreated {
                  order {
                    id
                  }
                }
              }
            }
            """,
            ["order_created"],
        ),
        (
            """
            fragment OrderFragment on Order {
              id
              number
              lines {
                id
              }
            }
            subscription {
              event {
                ...on OrderCreated {
                  order {
                    ...OrderFragment
                  }
                }
              }
            }
            """,
            ["order_created"],
        ),
        (
            """
            fragment OrderFragment on Order {
                id
            }

            fragment EventFragment on Event {
              issuedAt
              ... on OrderUpdated {
                order {
                    ... OrderFragment
                }
              }
            }

            subscription {
              event {
                ... EventFragment
              }
            }
            """,
            ["order_updated"],
        ),
        (
            """
            subscription {
              event{
                ... on OrderCreated{
                  order{
                    id
                  }
                }
                ... on OrderFullyPaid{
                  order{
                    id
                  }
                }
                ... on ProductCreated{
                  product{
                    id
                  }
                }
              }
            }
            """,
            ["order_created", "order_fully_paid", "product_created"],
        ),
        (
            """
            fragment MyFragment on Event {
                ... on OrderCreated{
                  order{
                    id
                  }
                }
                ... on OrderUpdated{
                  order{
                    id
                  }
                }
                ... on ProductCreated{
                  product{
                    id
                  }
                }
            }
            subscription {
                event {
                    ... MyFragment
                }
            }
            """,
            ["order_created", "order_updated", "product_created"],
        ),
        (
            """
            fragment EventFragment on Event {
              ... on OrderUpdated {
                order {
                    id
                }
              }
              ... on OrderCreated {
                order {
                    id
                }
              }
            }

            subscription {
              event {
                ... EventFragment
                ... on ProductCreated {
                    product {
                        id
                    }
                }
              }
            }
            """,
            ["order_updated", "order_created", "product_created"],
        ),
        (
            """
            subscription InvoiceRequested {
              event {
                ...InvoiceRequestedPayload
                }
              }
              fragment InvoiceRequestedPayload on InvoiceRequested {
                invoice {
                  id
                }
              }
            """,
            ["invoice_requested"],
        ),
        (
            """
            subscription{
              event{
                ...on ProductUpdated{
                  product{
                    id
                  }
                }
              }
              event{
                ...on ProductCreated{
                  product{
                    id
                  }
                }
              }
            }
            """,
            ["product_updated", "product_created"],
        ),
    ],
)
def test_get_event_type_from_subscription(query, events):
    subscription_query = SubscriptionQuery(query)
    assert subscription_query.is_valid
    assert subscription_query.events == sorted(events)


@pytest.mark.parametrize(
    ("query", "error_msg", "error_type", "error_code"),
    [
        (
            """
            mutation SomeMutation {
                someMutation(input: {}) {
                    result {
                        id
                    }
                }
            }
            """,
            'Cannot query field "someMutation" on type "Mutation".',
            GraphQLError,
            WebhookErrorCode.GRAPHQL_ERROR,
        ),
        (
            """
            subscription {
                event {
                    ... MyFragment
                }
            }
            """,
            'Unknown fragment "MyFragment".',
            GraphQLError,
            WebhookErrorCode.GRAPHQL_ERROR,
        ),
        (
            """
            fragment NotUsedEvents on Order {
              id
            }
            subscription {
              event {
                ... on OrderUpdated {
                  order {
                    id
                  }
                }
              }
            }
            """,
            'Fragment "NotUsedEvents" is never used.',
            GraphQLError,
            WebhookErrorCode.GRAPHQL_ERROR,
        ),
        (
            """
            query {{
            }
            """,
            "Syntax Error GraphQL (2:20) Expected Name, found",
            GraphQLSyntaxError,
            WebhookErrorCode.SYNTAX,
        ),
        (
            """
            query {
              channels {
                name
              }
            }
            """,
            "Subscription operation can't be found.",
            ValidationError,
            WebhookErrorCode.MISSING_SUBSCRIPTION,
        ),
        (
            """
            subscription {
              event {
                issuedAt
              }
            }
            """,
            "Can't find a single event.",
            ValidationError,
            WebhookErrorCode.MISSING_EVENT,
        ),
    ],
)
def test_query_validation(query, error_msg, error_type, error_code):
    subscription_query = SubscriptionQuery(query)
    assert not subscription_query.is_valid
    error = subscription_query.errors[0]
    assert isinstance(error, error_type)
    assert error_msg in error.message
    assert error_code.value == subscription_query.error_code


def test_get_events_from_field():
    # given
    query = """
        fragment EventFragment on Event {
          ... on OrderUpdated {
            order {
                id
            }
          }
        }
        subscription {
          event {
            ... on OrderCreated {
              order {
                id
              }
            }
            something
            somethingElse
            ... on OrderFullyPaid {
              order {
                id
              }
            }
            ... EventFragment
          }
        }
        """

    # when
    subscription_query = SubscriptionQuery(query)
    subscription = subscription_query._get_subscription(subscription_query.ast)
    event_fields = subscription_query._get_event_types_from_subscription(subscription)
    result = {}
    for event_field in event_fields:
        subscription_query._get_events_from_field(event_field, result)

    # then
    assert result == {
        "OrderCreated": IsFragment.FALSE,
        "OrderFullyPaid": IsFragment.FALSE,
        "EventFragment": IsFragment.TRUE,
    }
