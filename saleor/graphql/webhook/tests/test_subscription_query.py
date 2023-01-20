import pytest
from django.core.exceptions import ValidationError
from graphql import GraphQLError
from graphql.error import GraphQLSyntaxError

from ..subscription_query import (
    IsFragment,
    SubscriptionQuery,
    SubscriptionQueryErrorCode,
)


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
    "query,events",
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
    ],
)
def test_get_event_type_from_subscription(query, events):
    subscription_query = SubscriptionQuery(query)
    assert subscription_query.is_valid
    assert subscription_query.events == sorted(events)


@pytest.mark.parametrize(
    "query,error_msg,error_type",
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
        ),
        (
            """
            query {{
            }
            """,
            "Syntax Error GraphQL (2:20) Expected Name, found",
            GraphQLSyntaxError,
        ),
        (
            """
            query {
              channels {
                name
              }
            }
            """,
            SubscriptionQueryErrorCode.MISSING_SUBSCRIPTION.value,
            ValidationError,
        ),
        (
            """
            subscription {
              event {
                issuedAt
              }
            }
            """,
            SubscriptionQueryErrorCode.MISSING_EVENTS.value,
            ValidationError,
        ),
    ],
)
def test_query_validation(query, error_msg, error_type):
    subscription_query = SubscriptionQuery(query)
    assert not subscription_query.is_valid
    error = subscription_query.errors[0]
    assert isinstance(error, error_type)
    assert error_msg in error.message


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
    event_field = subscription_query._get_event_type_from_subscription(subscription)
    result = subscription_query._get_events_from_field(event_field)

    # then
    assert result == {
        "OrderCreated": IsFragment.FALSE,
        "OrderFullyPaid": IsFragment.FALSE,
        "EventFragment": IsFragment.TRUE,
    }
