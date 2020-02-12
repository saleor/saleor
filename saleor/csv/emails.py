from typing import TYPE_CHECKING

from templated_email import send_templated_mail

from ..core.emails import get_email_context
from ..core.utils import build_absolute_uri

if TYPE_CHECKING:
    from .models import Job


EXPORT_PRODUCTS_CSV_TEMPLATE = "csv/export_products_csv"


def send_link_to_download_csv_for_products(job: "Job"):
    recipient_email = job.user.email
    send_kwargs, ctx = get_email_context()
    ctx["csv_link"] = build_absolute_uri(job.content_file.url)
    send_templated_mail(
        template_name=EXPORT_PRODUCTS_CSV_TEMPLATE,
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )
