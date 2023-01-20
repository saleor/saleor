import pytest
from graphql import parse

from ..utils import (
    get_event_type_from_subscription,
    get_events_from_field,
    get_events_from_subscription,
    get_fragment_definitions,
    get_subscription,
)


@pytest.mark.parametrize(
    "query,event",
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
            fragment NotUsedEvents on Event {
              ... on OrderCreated {
                order {
                  id
                }
              }
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
            [],
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
            mutation SomeMutation {
                someMutation(input: {}) {
                    result {
                        id
                    }
                }
            }
            """,
            [],
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
            subscription {
                event {
                    ... MyFragment
                }
            }
            """,
            [],
        ),
        (
            """
            subscription {
              event {
                issuedAt
              }
            }
            """,
            [],
        ),
    ],
)
def test_get_event_type_from_subscription(query, event):
    assert sorted(get_events_from_subscription(query)) == sorted(event)


def test_get_events():
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
    ast = parse(query)
    subscription = get_subscription(ast)
    event_field = get_event_type_from_subscription(subscription)
    result = get_events_from_field(event_field)

    # then
    assert result == {
        "OrderCreated": "event",
        "OrderFullyPaid": "event",
        "EventFragment": "fragment",
    }


def test_get_fragment_definitions():
    # given
    query = """
        fragment OrderFragment on Order {
           order {
              id
            }
         }
        fragment EventFragment on Event {
          ... on OrderUpdated {
            ... OrderFragment
          }
        }
        subscription {
          event {
            ... on OrderCreated {
              order {
                id
              }
            }
          }
        }
        """

    # when
    ast = parse(query)
    result = get_fragment_definitions(ast)

    # then
    assert result["OrderFragment"]
    assert result["EventFragment"]
