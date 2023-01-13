import pytest

from ..utils import get_event_type_from_subscription


@pytest.mark.parametrize(
    "query,event",
    [
        (
            """
            subscription {
              event {
                ...on
                OrderCreated {
                  order {
                        id
                  }
                }
              }
            }
            """,
            "order_created",
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
            "order_created",
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
            "order_updated",
        ),
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
            "order_updated",
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
            None,
        ),
    ],
)
def test_get_event_type_from_subscription(query, event):
    assert get_event_type_from_subscription(query) == event
