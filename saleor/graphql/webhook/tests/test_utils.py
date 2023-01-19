import pytest
from graphql import parse

from ..utils import (
    get_event_field_from_subscription,
    get_event_type_from_subscription,
    get_events,
    get_fragments_from_field,
    get_subscription,
)


@pytest.mark.parametrize(
    "query,event",
    [
        # (
        #     """
        #     subscription {
        #       event {
        #         ...on OrderCreated {
        #           order {
        #             id
        #           }
        #         }
        #       }
        #     }
        #     """,
        #     ["order_created"],
        # ),
        # (
        #     """
        #     fragment OrderFragment on Order {
        #       id
        #       number
        #       lines {
        #         id
        #       }
        #     }
        #     subscription {
        #       event {
        #         ...on OrderCreated {
        #           order {
        #             ...OrderFragment
        #           }
        #         }
        #       }
        #     }
        #     """,
        #     ["order_created"],
        # ),
        # (
        #     """
        #     fragment NotUsedEvents on Event {
        #       ... on OrderCreated {
        #         order {
        #           id
        #         }
        #       }
        #     }
        #
        #     subscription {
        #       event {
        #         ... on OrderUpdated {
        #           order {
        #             id
        #           }
        #         }
        #       }
        #     }
        #     """,
        #     ["order_updated"],
        # ),
        (
            """
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
                ... EventFragment
              }
            }
            """,
            ["order_updated"],
        ),
        # (
        #     """
        #     mutation SomeMutation {
        #         someMutation(input: {}) {
        #             result {
        #                 id
        #             }
        #         }
        #     }
        #     """,
        #     [],
        # ),
        # (
        #     """
        #     subscription {
        #       event{
        #         ... on OrderCreated{
        #           order{
        #             id
        #           }
        #         }
        #         ... on OrderFullyPaid{
        #           order{
        #             id
        #           }
        #         }
        #         ... on ProductCreated{
        #           product{
        #             id
        #           }
        #         }
        #       }
        #     }
        #     """,
        #     ["order_created", "order_fully_paid", "product_created"],
        # ),
        # (
        #     """
        #     subscription {
        #         event {
        #             ... MyFragment
        #         }
        #     }
        #     """,
        #     [],
        # ),
    ],
)
def test_get_event_type_from_subscription(query, event):
    assert get_event_type_from_subscription(query) == event


def test_get_fragments_from_field():
    # given
    query = """
        subscription {
          event{
            ... on OrderCreated{
              order{
                ... FirstFragment
                someField {
                    id
                    nestedField {
                        ... SecondFragment
                    }
                    name
                }
              }
            }
          }
          ...ThirdFragment
        }
    """

    # when
    ast = parse(query)
    subscription = get_subscription(ast)
    fragments = {}
    result = get_fragments_from_field(subscription, fragments)

    # then
    assert result["FirstFragment"]
    assert result["SecondFragment"]
    assert result["ThirdFragment"]
    assert len(result) == 3


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
    event_field = get_event_field_from_subscription(subscription)
    result = get_events(event_field)

    # then
    assert result == {
        "OrderCreated": "event",
        "OrderFullyPaid": "event",
        "EventFragment": "fragment",
    }
