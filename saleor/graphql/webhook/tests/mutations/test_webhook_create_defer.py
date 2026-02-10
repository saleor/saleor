from .....webhook.error_codes import WebhookErrorCode
from .....webhook.models import Webhook
from ....tests.utils import get_graphql_content

WEBHOOK_CREATE_WITH_DEFER = """
    mutation webhookCreate($input: WebhookCreateInput!){
      webhookCreate(input: $input) {
        errors {
          field
          message
          code
        }
        webhook {
          id
          syncEvents {
            eventType
          }
        }
      }
    }
"""

CALCULATE_TAXES_QUERY_WITH_DEFER_IF = """
subscription {
  calculateTaxes(deferIf: [ADDRESS_MISSING]) {
    taxBase {
      currency
    }
  }
}
"""

CALCULATE_TAXES_QUERY_WITHOUT_DEFER_IF = """
subscription {
  calculateTaxes {
    taxBase {
      currency
    }
  }
}
"""


def test_webhook_create_with_defer_if_on_calculate_taxes(app_api_client):
    # given
    query = WEBHOOK_CREATE_WITH_DEFER
    variables = {
        "input": {
            "name": "Tax webhook with defer",
            "targetUrl": "https://www.example.com",
            "query": CALCULATE_TAXES_QUERY_WITH_DEFER_IF,
        }
    }

    # when
    response = app_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["webhookCreate"]
    assert not data["errors"]
    assert data["webhook"]

    new_webhook = Webhook.objects.get()
    assert new_webhook.defer_if_conditions == ["ADDRESS_MISSING"]


def test_webhook_create_without_defer_if_has_empty_conditions(app_api_client):
    # given
    query = WEBHOOK_CREATE_WITH_DEFER
    variables = {
        "input": {
            "name": "Tax webhook without defer",
            "targetUrl": "https://www.example.com",
            "query": CALCULATE_TAXES_QUERY_WITHOUT_DEFER_IF,
        }
    }

    # when
    response = app_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["webhookCreate"]
    assert not data["errors"]
    assert data["webhook"]

    new_webhook = Webhook.objects.get()
    assert new_webhook.defer_if_conditions == []


def test_webhook_create_defer_if_rejected_for_non_tax_event(app_api_client):
    # given - deferIf is only defined on calculateTaxes in the schema,
    # so using it on orderCreated causes a GraphQL validation error
    query = WEBHOOK_CREATE_WITH_DEFER
    non_tax_query_with_defer_if = """
    subscription {
      orderCreated(deferIf: [ADDRESS_MISSING]) {
        order {
          id
        }
      }
    }
    """
    variables = {
        "input": {
            "name": "Non-tax webhook with defer",
            "targetUrl": "https://www.example.com",
            "query": non_tax_query_with_defer_if,
        }
    }

    # when
    response = app_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    # then - schema validation rejects deferIf on non-tax subscription fields
    data = content["data"]["webhookCreate"]
    assert not data["webhook"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "query"
    assert "Unknown argument" in error["message"]
    assert error["code"] == WebhookErrorCode.GRAPHQL_ERROR.name
