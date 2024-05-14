import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from requests import HTTPError, RequestException

from .. import celeryconf
from ..core import JobStatus
from ..core.models import EventDelivery, EventDeliveryAttempt, EventPayload
from ..webhook.models import Webhook
from .installation_utils import AppInstallationError, install_app
from .models import App, AppExtension, AppInstallation, AppToken

logger = logging.getLogger(__name__)


@celeryconf.app.task
def install_app_task(job_id, activate=False):
    try:
        app_installation = AppInstallation.objects.get(id=job_id)
    except AppInstallation.DoesNotExist:
        logger.warning(
            "Failed to install app. AppInstallation not found for job_id: %s.", job_id
        )
        return
    try:
        app, _ = install_app(app_installation, activate=activate)
        app_installation.delete()
        app.is_installed = True
        app.save(update_fields=["is_installed"])
        return
    except ValidationError as e:
        msg = ", ".join([f"{name}: {err}" for name, err in e.message_dict.items()])
        app_installation.message = msg
    except AppInstallationError as e:
        logger.warning("Failed to install app. Error: %s", e)
        app_installation.set_message(str(e))
    except HTTPError as e:
        logger.warning(
            "Failed to install app. Response structure incorrect: missing error field."
            " Error: %s",
            e,
        )
        app_installation.message = (
            f"App internal error ({e.response.status_code}). "
            "Try later or contact with app support."
        )
    except RequestException as e:
        logger.warning("Failed to install app. Error: %s", e)
        app_installation.message = (
            "Failed to connect to app. Try later or contact with app support."
        )
    except Exception as e:
        logger.error("Failed to install app. Error: %s", e, exc_info=e)
        app_installation.message = "Unknown error. Contact with app support."
    app_installation.status = JobStatus.FAILED
    app_installation.save(update_fields=["message", "status"])


def _raw_remove_deliveries(deliveries_ids):
    deliveries = EventDelivery.objects.filter(id__in=deliveries_ids)
    payloads_ids = list(
        EventPayload.objects.filter(
            Exists(deliveries.filter(payload_id=OuterRef("id")))
        ).values_list("id", flat=True)
    )
    payloads = EventPayload.objects.filter(id__in=payloads_ids)
    attempts = EventDeliveryAttempt.objects.filter(
        Exists(deliveries.filter(id=OuterRef("delivery_id")))
    )
    attempts._raw_delete(attempts.db)  # type: ignore[attr-defined] # raw access # noqa: E501
    deliveries._raw_delete(deliveries.db)  # type: ignore[attr-defined] # raw access # noqa: E501
    payloads._raw_delete(payloads.db)  # type: ignore[attr-defined] # raw access # noqa: E501


@celeryconf.app.task
def remove_apps_task():
    app_delete_period = timezone.now() - settings.DELETE_APP_TTL
    apps = App.objects.filter(removed_at__lte=app_delete_period)

    # Saleor needs to remove app by app to prevent timeouts
    # on database when removing many deliveries.
    for app in apps.iterator():
        webhooks = Webhook.objects.filter(app_id=app.id)

        # Saleor uses batch size here to prevent timeouts on database.
        # Batch size determines how many deliveries will be removed,
        # each delivery contains attempts and payloads.
        batch_size = 1000
        last_id = 0
        while True:
            deliveries_ids = list(
                EventDelivery.objects.filter(
                    Q(id__gt=last_id),
                    Q(Exists(webhooks.filter(id=OuterRef("webhook_id")))),
                )
                .order_by("id")
                .values_list("id", flat=True)[:batch_size]
            )
            if not deliveries_ids:
                break
            last_id = deliveries_ids[-1]

            _raw_remove_deliveries(deliveries_ids)

        webhooks.delete()

        AppToken.objects.filter(app_id=app.id).delete()

        AppExtension.objects.filter(app_id=app.id).delete()

        app.delete()
