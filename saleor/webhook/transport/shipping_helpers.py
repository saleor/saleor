import base64

from ...app.models import App
from ..const import APP_ID_PREFIX


def to_shipping_app_id(app: App, shipping_method_id: str) -> str:
    app_identifier = app.identifier or app.id
    return base64.b64encode(
        str.encode(f"{APP_ID_PREFIX}:{app_identifier}:{shipping_method_id}")
    ).decode("utf-8")
