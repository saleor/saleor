from typing import TYPE_CHECKING

from templated_email import send_templated_mail

from ..celeryconf import app
from ..core.emails import get_email_context
from ..core.utils import build_absolute_uri

if TYPE_CHECKING:
    from .models import Job


EXPORT_TEMPLATES = {"export_products": "csv/export_products_csv"}


@app.task
def send_email_with_link_to_download_csv(job: "Job", template_name: str):
    recipient_email = job.created_by.email
    send_kwargs, ctx = get_email_context()
    ctx["csv_link"] = build_absolute_uri(job.content_file.url)
    send_templated_mail(
        template_name=EXPORT_TEMPLATES[template_name],
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )
