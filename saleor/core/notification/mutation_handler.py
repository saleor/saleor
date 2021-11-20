def get_external_notification_payload(objects, extra_payload, payload_function):
    return [
        _get_extracted_payload_input(payload_input, extra_payload, payload_function)
        for payload_input in objects
    ]


def send_notification(
    manager, external_event_type, payloads, channel_slug=None, plugin_id=None
):
    method_kwargs = dict(
        manager=manager,
        external_event_type=external_event_type,
        channel_slug=channel_slug,
        plugin_id=plugin_id,
    )
    if isinstance(payloads, list):
        for payload in payloads:
            trigger_notifications(**method_kwargs, payload=payload)
    else:
        trigger_notifications(**method_kwargs, payload=payloads)


def trigger_notifications(
    manager, external_event_type, payload, channel_slug=None, plugin_id=None
):
    method_kwargs = dict(event=external_event_type, payload=payload)
    manager.notify(**method_kwargs, plugin_id=plugin_id, channel_slug=channel_slug)


def _get_extracted_payload_input(payload_input, extra_payload, payload_function):
    payload = payload_function(payload_input)
    payload = payload[0] if type(payload) == list else payload
    payload.update({"extra_payload": extra_payload})
    return payload
