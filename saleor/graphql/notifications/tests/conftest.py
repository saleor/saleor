import json

import pytest
from django.contrib.auth.models import Permission


@pytest.fixture
def external_notification_trigger_query():
    return """
      mutation ExternalNotificationTrigger(
        $input: ExternalNotificationTriggerInput!
        $pluginId: String
      ) {
          externalNotificationTrigger(
            input: $input,
            pluginId: $pluginId
          ) {
            errors {
              message
            }
          }
      }
    """


@pytest.fixture
def manage_users_permission():
    return Permission.objects.get(codename="manage_users")


@pytest.fixture
def checkout_permission():
    return Permission.objects.get(codename="manage_checkouts")


@pytest.fixture
def order_permission():
    return Permission.objects.get(codename="manage_orders")


@pytest.fixture
def product_permission():
    return Permission.objects.get(codename="manage_products")


query_test_data = [
    (
        {
            "input": {
                "ids": [],
                "extraPayloads": json.dumps("{}"),
                "externalEventType": {},
            },
            "pluginId": "",
        },
        200,
    ),
    (
        {
            "input": {
                "ids": [],
                "extraPayloads": json.dumps("{}"),
                "externalEventType": {},
            },
            "pluginId": "WRONG-TEST-PLUGIN",
        },
        200,
    ),
    (
        {
            "input": {
                "ids": [],
                "extraPayloads": json.dumps("{}"),
                "externalEventType": {},
            }
        },
        200,
    ),
    (
        {"input": {"extraPayloads": json.dumps("{}"), "externalEventType": {}}},
        400,
    ),
    ({"input": {"ids": [], "externalEventType": {}}}, 400),
    (
        {
            "input": {
                "ids": [],
                "extraPayloads": json.dumps("{}"),
            }
        },
        400,
    ),
]
