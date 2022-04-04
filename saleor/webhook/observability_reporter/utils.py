from datetime import datetime, timedelta
from json.encoder import ESCAPE_ASCII, ESCAPE_DCT  # type: ignore
from typing import TYPE_CHECKING, Optional

from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from ..event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..models import Webhook

if TYPE_CHECKING:
    from celery.exceptions import Retry


class CustomJsonEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, JsonTruncText):
            return {"text": o.text, "truncated": o.truncated}
        return super().default(o)


def webhooks_for_event_exists(event_type, webhooks=None) -> bool:
    permissions = {}
    required_permission = WebhookEventAsyncType.PERMISSIONS.get(
        event_type, WebhookEventSyncType.PERMISSIONS.get(event_type)
    )
    if required_permission:
        app_label, codename = required_permission.value.split(".")
        permissions["app__permissions__content_type__app_label"] = app_label
        permissions["app__permissions__codename"] = codename

    if webhooks is None:
        webhooks = Webhook.objects.all()

    webhooks = webhooks.filter(
        is_active=True,
        app__is_active=True,
        events__event_type__in=[event_type, WebhookEventAsyncType.ANY],
        **permissions,
    )
    webhooks = webhooks.select_related("app").prefetch_related(
        "app__permissions__content_type"
    )
    return webhooks.exists()


def task_next_retry_date(retry_error: "Retry") -> Optional[datetime]:
    if isinstance(retry_error.when, (int, float)):
        return timezone.now() + timedelta(seconds=retry_error.when)
    if isinstance(retry_error.when, datetime):
        return retry_error.when
    return None


class JsonTruncText:
    def __init__(self, text="", truncated=False, added_bytes=0):
        self.text = text
        self.truncated = truncated
        self._added_bytes = max(0, added_bytes)

    def __eq__(self, other):
        if not isinstance(self, JsonTruncText):
            return False
        return (self.text, self.truncated) == (other.text, other.truncated)

    @property
    def byte_size(self) -> int:
        return len(self.text) + self._added_bytes

    @staticmethod
    def json_char_len(char: str) -> int:
        try:
            return len(ESCAPE_DCT[char])
        except KeyError:
            return 6 if ord(char) < 0x10000 else 12

    @classmethod
    def truncate(cls, s: str, limit: int):
        limit = max(limit, 0)
        s_init_len = len(s)
        s = s[:limit]
        added_bytes = 0

        for match in ESCAPE_ASCII.finditer(s):
            start, end = match.span(0)
            markup = cls.json_char_len(match.group(0)) - 1
            added_bytes += markup
            if end + added_bytes > limit:
                return cls(
                    text=s[:start],
                    truncated=True,
                    added_bytes=added_bytes - markup,
                )
            if end + added_bytes == limit:
                s = s[:end]
                return cls(
                    text=s,
                    truncated=len(s) < s_init_len,
                    added_bytes=added_bytes,
                )
        return cls(
            text=s,
            truncated=len(s) < s_init_len,
            added_bytes=added_bytes,
        )
