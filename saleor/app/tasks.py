from django.core.exceptions import ValidationError
from requests import HTTPError, RequestException

from .. import celeryconf
from ..core import JobStatus
from .installation_utils import install_app
from .models import AppInstallation


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
    except (RequestException, HTTPError):
        app_installation.message = (
            "Failed to connect to app. Try later or contact with app support."
        )
    except Exception:
        app_installation.message = "Unknow error. Contact with app support."
    app_installation.status = JobStatus.FAILED
    app_installation.save()
