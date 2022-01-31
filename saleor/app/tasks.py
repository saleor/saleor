import logging

from django.core.exceptions import ValidationError
from requests import HTTPError, RequestException

from .. import celeryconf
from ..core import JobStatus
from .installation_utils import install_app
from .models import AppInstallation

logger = logging.getLogger(__name__)


@celeryconf.app.task
def install_app_task(job_id, activate=False):
    app_installation = AppInstallation.objects.get(id=job_id)
    try:
        install_app(app_installation, activate=activate)
        app_installation.delete()
        return
    except ValidationError as e:
        msg = ", ".join([f"{name}: {err}" for name, err in e.message_dict.items()])
        app_installation.message = msg
    except (RequestException, HTTPError) as e:
        logger.warning("Failed to install an app. error: %s", e)
        app_installation.message = (
            "Failed to connect to app. Try later or contact with app support."
        )
    except Exception as e:
        logger.warning("Failed to install app. error %s", e)
        app_installation.message = "Unknown error. Contact with app support."
    app_installation.status = JobStatus.FAILED
    app_installation.save()
