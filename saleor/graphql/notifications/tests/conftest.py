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
