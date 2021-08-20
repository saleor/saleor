import json


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
    if plugin_id:
        manager.notify_in_single_plugin(plugin_id, external_event_type, payload)
    else:
        manager.notify(event=external_event_type, payload=payload)


def _get_extracted_payload_input(payload_input, extra_payload, payload_function):
    payload = json.loads(payload_function(payload_input))
    payload = payload[0] if type(payload) == list else payload
    payload.update({"extra_payload": extra_payload})
    return payload
