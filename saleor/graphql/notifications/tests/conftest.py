import json

import pytest


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
