from typing import Any, Dict, Union

from ..account.models import User
from ..app.models import App
from ..app.types import AppEventRequestorType, AppEventType
from .models import AppEvent

Requestor = Union[App, User, None]


def _requestor(requestor: Requestor) -> Dict:
    kwargs: Dict[str, Any] = {}
    parameters: Dict[str, Any] = {"requestor_type": AppEventRequestorType.SALEOR}
    if requestor:
        if isinstance(requestor, App):
            kwargs["app"] = requestor
            parameters["requestor_type"] = AppEventRequestorType.APP
        elif isinstance(requestor, User):
            kwargs["user"] = requestor
            parameters["requestor_type"] = AppEventRequestorType.USER
    kwargs["parameters"] = parameters
    return kwargs


def app_event_installed(app: App, *, requestor: Requestor) -> AppEvent:
    return AppEvent.objects.create(
        parent=app, type=AppEventType.INSTALLED, **_requestor(requestor)
    )


def app_event_activated(app: App, *, requestor: Requestor) -> AppEvent:
    return AppEvent.objects.create(
        parent=app, type=AppEventType.ACTIVATED, **_requestor(requestor)
    )


def app_event_deactivated(app: App, *, requestor: Requestor) -> AppEvent:
    return AppEvent.objects.create(
        parent=app, type=AppEventType.DEACTIVATED, **_requestor(requestor)
    )
