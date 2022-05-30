from datetime import datetime
from enum import Enum
from json.encoder import ESCAPE_ASCII, ESCAPE_DCT  # type: ignore
from typing import List, Optional, Tuple, TypedDict


class JsonTruncText:
    def __init__(self, text="", truncated=False, added_bytes=0):
        self.text = text
        self.truncated = truncated
        self._added_bytes = max(0, added_bytes)

    def __eq__(self, other):
        if not isinstance(other, JsonTruncText):
            return False
        return (self.text, self.truncated) == (other.text, other.truncated)

    def __repr__(self):
        return f'JsonTruncText(text="{self.text}", truncated={self.truncated})'

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


class ObservabilityEventTypes(str, Enum):
    API_CALL = "api_call"
    EVENT_DELIVERY_ATTEMPT = "event_delivery_attempt"


HttpHeaders = List[Tuple[str, str]]


class App(TypedDict):
    id: str
    name: str


class Webhook(TypedDict):
    id: str
    name: str
    target_url: str
    subscription_query: Optional[JsonTruncText]


class ObservabilityEventBase(TypedDict):
    event_type: ObservabilityEventTypes


class GraphQLOperation(TypedDict):
    name: Optional[JsonTruncText]
    operation_type: Optional[str]
    query: Optional[JsonTruncText]
    result: Optional[JsonTruncText]
    result_invalid: bool


class ApiCallRequest(TypedDict):
    id: str
    method: str
    url: str
    time: float
    headers: HttpHeaders
    content_length: int


class ApiCallResponse(TypedDict):
    headers: HttpHeaders
    status_code: Optional[int]
    content_length: int


class ApiCallPayload(ObservabilityEventBase):
    request: ApiCallRequest
    response: ApiCallResponse
    app: Optional[App]
    gql_operations: List[GraphQLOperation]


class EventDeliveryPayload(TypedDict):
    content_length: int
    body: JsonTruncText


class EventDelivery(TypedDict):
    id: str
    status: str
    event_type: str
    event_sync: bool
    payload: EventDeliveryPayload


class EventDeliveryAttemptRequest(TypedDict):
    headers: HttpHeaders


class EventDeliveryAttemptResponse(TypedDict):
    headers: HttpHeaders
    status_code: Optional[int]
    content_length: int
    body: JsonTruncText


class EventDeliveryAttemptPayload(ObservabilityEventBase):
    id: str
    time: datetime
    duration: Optional[float]
    status: str
    next_retry: Optional[datetime]
    request: EventDeliveryAttemptRequest
    response: EventDeliveryAttemptResponse
    event_delivery: EventDelivery
    webhook: Webhook
    app: App
