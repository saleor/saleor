import base64

from ...app.models import App
from ..const import APP_ID_PREFIX


def to_shipping_app_id(app: App, shipping_method_id: str) -> str:
    app_identifier = app.identifier or app.id
    return base64.b64encode(
        str.encode(f"{APP_ID_PREFIX}:{app_identifier}:{shipping_method_id}")
    ).decode("utf-8")


def convert_to_app_id_with_identifier(shipping_app_id: str) -> None | str:
    """Prepare the shipping_app_id in format `app:<app-identifier>:method_id>`.

    The format of shipping_app_id has been changes so we need to support both of them.
    This method is preparing the new shipping_app_id format based on assumptions
    that right now the old one is used which is `app:<app-pk>:<method_id>`
    """
    decoded_id = base64.b64decode(shipping_app_id).decode()
    splitted_id = decoded_id.split(":")
    if len(splitted_id) != 3:
        return None
    try:
        app_id = int(splitted_id[1])
    except (TypeError, ValueError):
        return None
    app = App.objects.filter(id=app_id).first()
    if app is None:
        return None
    return to_shipping_app_id(app, splitted_id[2])
