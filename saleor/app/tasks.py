from django.core.exceptions import ValidationError
from requests import RequestException

from .. import celeryconf
from ..core import JobStatus
from .installation_utils import install_app
from .models import AppJob


@celeryconf.app.task
def install_app_task(job_id):
    app_job = AppJob.objects.get(id=job_id)
    try:
        install_app(app_job.manifest_url, app_job.permissions.all())
        app_job.delete()
        return
    except ValidationError:
        app_job.message = (
            "token_target_url has inccorrect format. Contact with app support."
        )
    except RequestException:
        app_job.message = (
            "Failed to connect to app. Try later or contact with app support."
        )
    except Exception:
        app_job.message = "Unknow error. Concact with app support."
    app_job.status = JobStatus.FAILED
    app_job.save()
