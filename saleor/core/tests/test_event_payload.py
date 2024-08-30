import pytest
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from storages.utils import safe_join

from ..models import EventPayload


@pytest.fixture
def payload_data():
    return '{\n    "product": {\n        "name": "Żółta ćma"\n    }\n}\n'


def test_reading_event_payload(payload_data):
    # given
    payload = EventPayload.objects.create()
    payload.save_payload_file(payload_data)

    # when
    read_payload = payload.get_payload()

    # then
    assert read_payload == payload_data


def test_reading_event_payload_saved_as_string(payload_data):
    # given
    # Force saving payload as string (as old payloads were)
    payload = EventPayload.objects.create()
    prefix = get_random_string(length=12)
    file_name = f"{payload.pk}.json"
    file_path = safe_join(prefix, file_name)
    payload.payload_file.save(file_path, ContentFile(payload_data))

    # when
    read_payload = payload.get_payload()

    # then
    assert read_payload == payload_data
