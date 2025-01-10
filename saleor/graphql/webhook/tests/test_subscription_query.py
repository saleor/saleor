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


SUBSCRIPTION_ORDER_CREATED = """
subscription {
  event {
    ...on OrderCreated {
      order {
        id
      }
    }
  }
}
"""

SUBSCRIPTION_ORDER_CREATED_WITH_FRAGMENT = """
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
"""

SUBSCRIPTION_ORDER_UPDATED_WITH_FRAGMENT = """
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
"""

SUBSCRIPTION_MULTIPLE_EVENTS = """
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
"""

SUBSCRIPTION_MULTIPLE_EVENTS_WITH_FRAGMENT = """
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
"""

SUBSCRIPTION_MULTIPLE_EVENTS_WITH_PARTIALLY_FRAGMENT = """
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

SUBSCRIPTION_INVOICE_REQUESTED_WITH_FRAGMENT = """
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
"""

SUBSCRIPTION_WITH_MULTIPLE_EVENT_FIELD = """
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
"""

SUBSCRIPTION_FILTERABLE_ORDER_CREATED = """
subscription{
    orderCreated(channels:["default"]){
        order{
            id
        }
    }
}
"""

SUBSCRIPTION_FILTERABLE_ORDER_CREATED_WITH_FRAGMENT = """
fragment OrderFragment on Order {
  id
  number
  lines {
    id
  }
}
subscription {
  orderCreated{
    order{
      ...OrderFragment
    }
  }
}
"""

SUBSCRIPTION_FILTERABLE_WITHOUT_ARGUMENTS = """
fragment OrderFragment on Order {
  id
  number
  lines {
    id
  }
}
subscription {
    updated: orderUpdated{
        order{
            ...OrderFragment
        }
    }
}
"""


@pytest.mark.parametrize(
    ("query", "events"),
    [
        (
            SUBSCRIPTION_ORDER_CREATED,
            ["order_created"],
        ),
        (
            SUBSCRIPTION_ORDER_CREATED_WITH_FRAGMENT,
            ["order_created"],
        ),
        (
            SUBSCRIPTION_ORDER_UPDATED_WITH_FRAGMENT,
            ["order_updated"],
        ),
        (
            SUBSCRIPTION_MULTIPLE_EVENTS,
            ["order_created", "order_fully_paid", "product_created"],
        ),
        (
            SUBSCRIPTION_MULTIPLE_EVENTS_WITH_FRAGMENT,
            ["order_created", "order_updated", "product_created"],
        ),
        (
            SUBSCRIPTION_MULTIPLE_EVENTS_WITH_PARTIALLY_FRAGMENT,
            ["order_updated", "order_created", "product_created"],
        ),
        (
            SUBSCRIPTION_INVOICE_REQUESTED_WITH_FRAGMENT,
            ["invoice_requested"],
        ),
        (
            SUBSCRIPTION_WITH_MULTIPLE_EVENT_FIELD,
            ["product_updated", "product_created"],
        ),
        (
            SUBSCRIPTION_FILTERABLE_ORDER_CREATED,
            ["order_created"],
        ),
        (
            SUBSCRIPTION_FILTERABLE_ORDER_CREATED_WITH_FRAGMENT,
            ["order_created"],
        ),
        (
            SUBSCRIPTION_FILTERABLE_WITHOUT_ARGUMENTS,
            ["order_updated"],
        ),
    ],
)
def test_get_event_type_from_subscription(query, events):
    subscription_query = SubscriptionQuery(query)
    assert subscription_query.is_valid
    assert subscription_query.events == sorted(events)


SUBSCRIPTION_MUTATION_AS_INPUT = """
mutation SomeMutation {
    someMutation(input: {}) {
        result {
            id
        }
    }
}
"""
SUBSCRIPTION_UNKNOWN_FRAGMENT = """
subscription {
    event {
        ... MyFragment
    }
}
"""

SUBSCRIPTION_NOT_USED_FRAGMENT = """
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
"""
SUBSCRIPTION_SYNTAX_ERROR = """
query {{
}
"""

SUBSCRIPTION_QUERY_USED = """
query {
  channels {
    name
  }
}
"""
SUBSCRIPTION_MISSING_EVENT = """
subscription {
  event {
    issuedAt
  }
}
"""
SUBSCRIPTION_FILTERABLE_ORDER_CREATED_AND_EVENT_MANY_TOP_FIELDS = """
subscription {
    event{
        ...on OrderCreated{
            order{
                id
            }
        }
    }
    orderCreated(channels:["default-channel"]){
        order{
            lines{
                id
                variant{
                    id
                    product{
                        id
                    }
                }
            }
        }
    }
}
"""
SUBSCRIPTION_MANY_TOP_FILTERABLE_FIELDS = """
subscription {
    orderCreated(channels:["default-channel"]){
        order{
            lines{
                id
                variant{
                    id
                    product{
                        id
                    }
                }
            }
        }
    }
    orderCreated(channels:["default-channel"]){
        order{
            lines{
                id
                variant{
                    id
                    product{
                        id
                    }
                }
            }
        }
    }
}
"""

SUBSCRIPTION_MANY_TOP_FILTERABLE_FIELDS_WITH_ALIAS = """
subscription {
    alias: orderCreated(channels:["default-channel"]){
        order{
            lines{
                id
                variant{
                    id
                    product{
                        id
                    }
                }
            }
        }
    }
    orderCreated(channels:["default-channel"]){
        order{
            lines{
                id
                variant{
                    id
                    product{
                        id
                    }
                }
            }
        }
    }
}
"""

SUBSCRIPTION_MANY_TOP_FILTERABLE_DIFFERENT_FIELDS = """
subscription {
    orderUpdated(channels:["default-channel"]){
        order{
            lines{
                id
                variant{
                    id
                    product{
                        id
                    }
                }
            }
        }
    }
    orderCreated(channels:["default-channel"]){
        order{
            lines{
                id
                variant{
                    id
                    product{
                        id
                    }
                }
            }
        }
    }
}
"""
SUBSCRIPTION_MANY_TOP_FILTERABLE_DIFFERENT_FIELDS_WITH_ALIAS = """
subscription {
    alias: orderUpdated(channels:["different-channel"]){
        order{
            lines{
                id
                variant{
                    id
                    product{
                        id
                    }
                }
            }
        }
    }
    orderCreated(channels:["default-channel"]){
        order{
            lines{
                id
                variant{
                    id
                    product{
                        id
                    }
                }
            }
        }
    }
}
"""


@pytest.mark.parametrize(
    ("query", "error_msg", "error_type", "error_code"),
    [
        (
            SUBSCRIPTION_MUTATION_AS_INPUT,
            'Cannot query field "someMutation" on type "Mutation".',
            GraphQLError,
            WebhookErrorCode.GRAPHQL_ERROR,
        ),
        (
            SUBSCRIPTION_UNKNOWN_FRAGMENT,
            'Unknown fragment "MyFragment".',
            GraphQLError,
            WebhookErrorCode.GRAPHQL_ERROR,
        ),
        (
            SUBSCRIPTION_NOT_USED_FRAGMENT,
            'Fragment "NotUsedEvents" is never used.',
            GraphQLError,
            WebhookErrorCode.GRAPHQL_ERROR,
        ),
        (
            SUBSCRIPTION_SYNTAX_ERROR,
            "Syntax Error GraphQL (2:8) Expected Name, found",
            GraphQLSyntaxError,
            WebhookErrorCode.SYNTAX,
        ),
        (
            SUBSCRIPTION_QUERY_USED,
            "Subscription operation can't be found.",
            ValidationError,
            WebhookErrorCode.MISSING_SUBSCRIPTION,
        ),
        (
            SUBSCRIPTION_MISSING_EVENT,
            "Can't find a single event.",
            ValidationError,
            WebhookErrorCode.MISSING_EVENT,
        ),
        (
            SUBSCRIPTION_FILTERABLE_ORDER_CREATED_AND_EVENT_MANY_TOP_FIELDS,
            "Subscription must select only one top field.",
            ValidationError,
            WebhookErrorCode.INVALID,
        ),
        (
            SUBSCRIPTION_MANY_TOP_FILTERABLE_FIELDS,
            "Subscription must select only one top field.",
            ValidationError,
            WebhookErrorCode.INVALID,
        ),
        (
            SUBSCRIPTION_MANY_TOP_FILTERABLE_FIELDS_WITH_ALIAS,
            "Subscription must select only one top field.",
            ValidationError,
            WebhookErrorCode.INVALID,
        ),
        (
            SUBSCRIPTION_MANY_TOP_FILTERABLE_DIFFERENT_FIELDS,
            "Subscription must select only one top field.",
            ValidationError,
            WebhookErrorCode.INVALID,
        ),
        (
            SUBSCRIPTION_MANY_TOP_FILTERABLE_DIFFERENT_FIELDS_WITH_ALIAS,
            "Subscription must select only one top field.",
            ValidationError,
            WebhookErrorCode.INVALID,
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


def test_get_filterable_channel_slugs_for_query_with_filters():
    # given
    query = """
    subscription {
      orderConfirmed(channels: ["default-channel"]) {
        order {
          id
          number
          lines {
            id
            variant {
              id
            }
          }
        }
      }
    }
    """
    subscription_query = SubscriptionQuery(query)

    # when
    result = subscription_query.get_filterable_channel_slugs()

    # then
    assert result == ["default-channel"]


def test_get_filterable_channel_slugs_with_empty_filters():
    # given
    query = """
    subscription {
      orderConfirmed {
        order {
          id
          number
          lines {
            id
            variant {
              id
            }
          }
        }
      }
    }
    """
    subscription_query = SubscriptionQuery(query)

    # when
    result = subscription_query.get_filterable_channel_slugs()

    # then
    assert result == []


def test_get_filterable_channel_slugs_for_non_filterable_query():
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
    subscription_query = SubscriptionQuery(query)

    # when
    result = subscription_query.get_filterable_channel_slugs()

    # then
    assert result == []
