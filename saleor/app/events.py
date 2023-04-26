from typing import Any, Dict, Union

from ..account.models import User
from ..app.models import App
from ..app.types import AppEventRequestorType, AppEventType
from .models import AppEvent

Requestor = Union[App, User, None]


def _requestor(requestor: Requestor) -> Dict:
    kwargs: Dict[str, Any] = {"requestor_type": AppEventRequestorType.SALEOR}
    if requestor:
        if isinstance(requestor, App):
            kwargs["requestor_type"] = AppEventRequestorType.APP
            kwargs["requestor_app"] = requestor
        elif isinstance(requestor, User):
            kwargs["requestor_type"] = AppEventRequestorType.USER
            kwargs["requestor_user"] = requestor
    return kwargs


def app_event_installed(app: App, *, requestor: Requestor) -> AppEvent:
    return AppEvent.objects.create(
        app=app, type=AppEventType.INSTALLED, **_requestor(requestor)
    )


def app_event_activated(app: App, *, requestor: Requestor) -> AppEvent:
    return AppEvent.objects.create(
        app=app, type=AppEventType.ACTIVATED, **_requestor(requestor)
    )


def app_event_deactivated(app: App, *, requestor: Requestor) -> AppEvent:
    return AppEvent.objects.create(
        app=app, type=AppEventType.DEACTIVATED, **_requestor(requestor)
    )
