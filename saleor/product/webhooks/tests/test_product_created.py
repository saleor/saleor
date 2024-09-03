from unittest import mock

from ..product_created import ProductCreated


@mock.patch("saleor.webhook.utils.get_webhooks_for_event")
@mock.patch("saleor.webhook.transport.asynchronous.transport.trigger_webhooks_async")
def test_product_created_trigger(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    product,
    django_capture_on_commit_callbacks,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]

    # when
    with django_capture_on_commit_callbacks(execute=True):
        ProductCreated.trigger_webhook_async(product)

    # then
    mocked_webhook_trigger.assert_called_once_with(
        data=None,
        event_type=ProductCreated,
        webhooks=[any_webhook],
        subscribable_object=product,
        requestor=None,
        legacy_data_generator=mock.ANY,
        allow_replica=True,
    )
