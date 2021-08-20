def get_external_notification_payload(objects, extra_payload, payload_function):
    return [
        _get_extracted_payload_input(payload_input, extra_payload, payload_function)
        for payload_input in objects
    ]


def send_notification(manager, external_event_type, payloads, plugin_id=None):
    if isinstance(payloads, list):
        for payload in payloads:
            trigger_notifications(manager, external_event_type, payload, plugin_id)
    else:
        trigger_notifications(manager, external_event_type, payloads, plugin_id)


def trigger_notifications(manager, external_event_type, payload, plugin_id=None):
    method_kwargs = dict(event=external_event_type, payload=payload)
    manager.notify(**method_kwargs, plugin_id=plugin_id)


def _get_extracted_payload_input(payload_input, extra_payload, payload_function):
    payload = payload_function(payload_input)
    payload = payload[0] if type(payload) == list else payload
    payload.update({"extra_payload": extra_payload})
    return payload
