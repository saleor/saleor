from unittest.mock import patch

import pytest

from ..obfuscation import (
    MASK,
    anonymize_event_payload,
    anonymize_gql_operation_response,
    filter_and_hide_headers,
)


@pytest.mark.parametrize(
    ("headers", "allowed", "sensitive", "expected"),
    [
        ({}, {"header"}, {"header"}, {}),
        ({"Header": "val"}, {}, {}, {}),
        ({"HeAdEr": "val"}, {"header"}, {}, {"HeAdEr": "val"}),
        (
            {"Header": "val", "AuThOrIzAtIoN": "secret"},
            {"header"},
            {"authorization"},
            {"Header": "val"},
        ),
        (
            {"Content-Length": "10", "AuThOrIzAtIoN": "secret", "Not-Allowed": "val"},
            {"content-length", "authorization"},
            {"authorization"},
            {"Content-Length": "10", "AuThOrIzAtIoN": MASK},
        ),
    ],
)
def test_filter_and_hide_headers(headers, allowed, sensitive, expected):
    assert (
        filter_and_hide_headers(headers, allowed=allowed, sensitive=sensitive)
        == expected
    )


def test_anonymize_gql_operation_response(gql_operation_factory):
    query = 'query FirstQuery { order(id: "test") { user { email } } }'
    result = {"data": "result"}
    operation_result = gql_operation_factory(query, result=result)

    anonymize_gql_operation_response(operation_result)

    assert operation_result.result["data"] == MASK


def test_anonymize_gql_operation_with_mutation_in_query(gql_operation_factory):
    query = """
    mutation tokenRefresh($token: String){
        tokenRefresh(refreshToken: $token){
            token
        }
    }"""
    result = {"data": {"tokenRefresh": {"token": "SECRET TOKEN"}}}
    operation_result = gql_operation_factory(query, result=result)

    anonymize_gql_operation_response(operation_result)

    assert operation_result.result["data"] == MASK


@patch(
    "saleor.webhook.observability.obfuscation.SENSITIVE_GQL_FIELDS",
    {"Product": {"name"}},
)
def test_anonymize_gql_operation_with_subscription_in_query(gql_operation_factory):
    query = """
    subscription{
      event{
        ...on ProductUpdated{
          product{
            id
            name
          }
        }
      }
    }
    """
    result = {"data": "secret data"}
    operation_result = gql_operation_factory(query, result=result)

    anonymize_gql_operation_response(operation_result)

    assert operation_result.result["data"] == MASK


@patch(
    "saleor.webhook.observability.obfuscation.SENSITIVE_GQL_FIELDS",
    {"Product": {"name"}},
)
def test_anonymize_gql_operation_response_with_fragment_spread(gql_operation_factory):
    query = """
    fragment ProductFragment on Product {
      id
      name
    }
    query products($first: Int){
      products(channel: "channel-pln", first:$first){
        edges{
          node{
            ... ProductFragment
            variants {
                variantName: name
            }
          }
        }
      }
    }"""
    result = {"data": "result"}
    operation_result = gql_operation_factory(query, result=result)

    anonymize_gql_operation_response(operation_result)

    assert operation_result.result["data"] == MASK


@patch(
    "saleor.webhook.observability.obfuscation.SENSITIVE_GQL_FIELDS",
    {"Product": {"name"}},
)
def test_anonymize_event_payload():
    query = """
        subscription{
          event{
            ...on ProductUpdated{
              product{
                id
                name
              }
            }
          }
        }
        """
    payload = [{"sensitive": "data"}]

    anonymized = anonymize_event_payload(query, "any_type", payload)

    assert anonymized == MASK


@patch(
    "saleor.webhook.observability.obfuscation.SENSITIVE_GQL_FIELDS",
    {"Product": {"name"}},
)
def test_anonymize_event_delivery_payload_when_empty_subscription_query():
    payload = [{"sensitive": "data"}]

    anonymized = anonymize_event_payload(None, "any_type", payload)

    assert anonymized == payload
