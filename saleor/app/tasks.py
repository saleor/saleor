from django.core.exceptions import ValidationError
from requests import HTTPError, RequestException

from .. import celeryconf
from ..core import JobStatus
from .installation_utils import install_app
from .models import AppJob


@celeryconf.app.task
def install_app_task(job_id, activate=False):
    app_job = AppJob.objects.get(id=job_id)
    try:
        install_app(app_job, activate=activate)
        app_job.delete()
        return
    except ValidationError as e:
        msg = ", ".join([f"{name}: {err}" for name, err in e.message_dict.items()])
        app_job.message = msg
    except (RequestException, HTTPError):
        app_job.message = (
            "Failed to connect to app. Try later or contact with app support."
        )
    except Exception:
        app_job.message = "Unknow error. Contact with app support."
    app_job.status = JobStatus.FAILED
    app_job.save()
