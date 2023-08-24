from typing import TYPE_CHECKING

from ..core.notification.utils import get_site_context
from ..core.notify_events import NotifyEventType
from ..core.utils import build_absolute_uri
from ..graphql.core.utils import to_global_id_or_none
from ..plugins.manager import get_plugins_manager

if TYPE_CHECKING:
    from .models import ExportFile


def get_default_export_payload(export_file: "ExportFile") -> dict:
    user_id = to_global_id_or_none(export_file.user) if export_file.user else None
    user_email = export_file.user.email if export_file.user else None
    app_id = to_global_id_or_none(export_file.app) if export_file.app else None
    return {
        "user_id": user_id,
        "user_email": user_email,
        "app_id": app_id,
        "id": to_global_id_or_none(export_file),
        "status": export_file.status,
        "message": export_file.message,
        "created_at": export_file.created_at,
        "updated_at": export_file.updated_at,
    }


def send_export_download_link_notification(export_file: "ExportFile", data_type: str):
    """Call PluginManager.notify to trigger the notification for success export."""
    payload = {
        "export": get_default_export_payload(export_file),
        "csv_link": build_absolute_uri(export_file.content_file.url),
        "recipient_email": export_file.user.email if export_file.user else None,
        "data_type": data_type,
        **get_site_context(),
    }

    manager = get_plugins_manager()
    manager.notify(NotifyEventType.CSV_EXPORT_SUCCESS, payload)
    if data_type == "gift cards":
        manager.gift_card_export_completed(export_file)
    if data_type == "products":
        manager.product_export_completed(export_file)


def send_export_failed_info(export_file: "ExportFile", data_type: str):
    """Call PluginManager.notify to trigger the notification for failed export."""
    payload = {
        "export": get_default_export_payload(export_file),
        "recipient_email": export_file.user.email if export_file.user else None,
        "data_type": data_type,
        **get_site_context(),
    }
    manager = get_plugins_manager()
    manager.notify(NotifyEventType.CSV_EXPORT_FAILED, payload)
    if data_type == "gift cards":
        manager.gift_card_export_completed(export_file)
    if data_type == "products":
        manager.product_export_completed(export_file)
