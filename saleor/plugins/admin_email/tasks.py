from ...celeryconf import app
from ...csv.events import export_failed_info_sent_event, export_file_sent_event
from ...graphql.core.utils import from_global_id_or_none
from ..email_common import EmailConfig, send_email


@app.task(compression="zlib")
def send_set_staff_password_email_task(
    recipient_email, payload, config: dict, subject, template
):
    email_config = EmailConfig(**config)
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=template,
    )


@app.task(compression="zlib")
def send_email_with_link_to_download_file_task(
    recipient_email: str, payload, config: dict, subject, template
):
    email_config = EmailConfig(**config)
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        subject=subject,
        template_str=template,
        context=payload,
    )
    export_file_sent_event(
        export_file_id=from_global_id_or_none(payload["export"]["id"]),
        user_id=from_global_id_or_none(payload["export"].get("user_id")),
    )


@app.task(compression="zlib")
def send_export_failed_email_task(
    recipient_email: str, payload: dict, config: dict, subject, template
):
    email_config = EmailConfig(**config)
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        subject=subject,
        template_str=template,
        context=payload,
    )
    export_failed_info_sent_event(
        export_file_id=from_global_id_or_none(payload["export"]["id"]),
        user_id=from_global_id_or_none(payload["export"].get("user_id")),
    )


@app.task(compression="zlib")
def send_staff_order_confirmation_email_task(
    recipient_list: str, payload: dict, config: dict, subject, template
):
    email_config = EmailConfig(**config)
    send_email(
        config=email_config,
        recipient_list=recipient_list,
        subject=subject,
        template_str=template,
        context=payload,
    )


@app.task(compression="zlib")
def send_staff_password_reset_email_task(
    recipient_email, payload, config, subject, template
):
    email_config = EmailConfig(**config)
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=template,
    )
