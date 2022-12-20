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
    ],
)
def test_get_event_type_from_subscription(query, event):
    assert get_event_type_from_subscription(query) == event
