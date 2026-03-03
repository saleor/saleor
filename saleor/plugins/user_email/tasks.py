import logging
from email.headerregistry import Address

import pybars
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend

from ...account import events as account_events
from ...celeryconf import app
from ...core.db.connection import allow_writer
from ...core.http_client import HTTPClient
from ...giftcard import events as gift_card_events
from ...graphql.core.utils import from_global_id_or_none
from ...invoice import events as invoice_events
from ...order import events as order_events
from ..email_common import (
    DEFAULT_EMAIL_TIMEOUT,
    EmailConfig,
    compare,
    format_address,
    format_datetime,
    get_plain_text_message_for_email,
    get_product_image_thumbnail,
    price,
    send_email,
)

logger = logging.getLogger(__name__)


@app.task(compression="zlib")
def send_account_confirmation_email_task(
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


@app.task(compression="zlib")
def send_password_reset_email_task(recipient_email, payload, config, subject, template):
    user_id = payload.get("user", {}).get("id")
    email_config = EmailConfig(**config)

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=template,
    )
    with allow_writer():
        account_events.customer_password_reset_link_sent_event(
            user_id=from_global_id_or_none(user_id)
        )


@app.task(compression="zlib")
def send_request_email_change_email_task(
    recipient_email, payload, config, subject, template
):
    user_id = payload.get("user", {}).get("id")
    email_config = EmailConfig(**config)

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=template,
    )
    with allow_writer():
        account_events.customer_email_change_request_event(
            user_id=from_global_id_or_none(user_id),
            parameters={
                "old_email": payload.get("old_email"),
                "new_email": recipient_email,
            },
        )


@app.task(compression="zlib")
def send_user_change_email_notification_task(
    recipient_email, payload, config, subject, template
):
    user_id = payload.get("user", {}).get("id")
    email_config = EmailConfig(**config)

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=template,
    )
    event_parameters = {
        "old_email": payload.get("old_email"),
        "new_email": payload.get("new_email"),
    }
    with allow_writer():
        account_events.customer_email_changed_event(
            user_id=from_global_id_or_none(user_id), parameters=event_parameters
        )


@app.task(compression="zlib")
def send_account_delete_confirmation_email_task(
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


@app.task(compression="zlib")
def send_set_user_password_email_task(
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


@app.task(compression="zlib")
def send_gift_card_email_task(recipient_email, payload, config, subject, template):
    email_config = EmailConfig(**config)
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=template,
    )
    email_data = {
        "gift_card_id": from_global_id_or_none(payload["gift_card"]["id"]),
        "user_id": from_global_id_or_none(payload["requester_user_id"]),
        "app_id": from_global_id_or_none(payload["requester_app_id"]),
        "email": payload["recipient_email"],
    }
    with allow_writer():
        if payload["resending"] is True:
            gift_card_events.gift_card_resent_event(**email_data)
        else:
            gift_card_events.gift_card_sent_event(**email_data)


@app.task(compression="zlib")
def send_invoice_email_task(recipient_email, payload, config, subject, template):
    """Send an invoice to user of related order with URL to download it."""
    email_config = EmailConfig(**config)
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=template,
    )
    with allow_writer():
        invoice_events.notification_invoice_sent_event(
            user_id=from_global_id_or_none(payload["requester_user_id"]),
            app_id=from_global_id_or_none(payload["requester_app_id"]),
            invoice_id=from_global_id_or_none(payload["invoice"]["id"]),
            customer_email=payload["recipient_email"],
        )
        order_events.event_invoice_sent_notification(
            order_id=from_global_id_or_none(payload["invoice"]["order_id"]),
            user_id=from_global_id_or_none(payload["requester_user_id"]),
            app_id=from_global_id_or_none(payload["requester_app_id"]),
            email=payload["recipient_email"],
        )


@app.task(compression="zlib")
def send_order_confirmation_email_task(
    recipient_email, payload, config, subject, template
):
    """Send order confirmation email."""
    email_config = EmailConfig(**config)
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=template,
    )
    with allow_writer():
        order_events.event_order_confirmation_notification(
            order_id=from_global_id_or_none(payload["order"]["id"]),
            user_id=from_global_id_or_none(payload["order"].get("user_id")),
            customer_email=recipient_email,
        )


@app.task(compression="zlib")
def send_fulfillment_confirmation_email_task(
    recipient_email, payload, config, subject, template
):
    email_config = EmailConfig(**config)

    compiler = pybars.Compiler()
    helpers = {
        "format_address": format_address,
        "price": price,
        "format_datetime": format_datetime,
        "get_product_image_thumbnail": get_product_image_thumbnail,
        "compare": compare,
    }
    html_message = str(compiler.compile(template)(payload, helpers=helpers))
    subject_message = str(compiler.compile(subject)(payload, helpers))
    plain_text = get_plain_text_message_for_email(html_message)

    from_email = str(
        Address(email_config.sender_name or "", addr_spec=email_config.sender_address)
    )
    backend = EmailBackend(
        host=email_config.host,
        port=email_config.port,
        username=email_config.username,
        password=email_config.password,
        use_ssl=email_config.use_ssl,
        use_tls=email_config.use_tls,
        timeout=DEFAULT_EMAIL_TIMEOUT,
    )

    email = EmailMultiAlternatives(
        subject=subject_message,
        body=plain_text,
        from_email=from_email,
        to=[recipient_email],
        bcc=settings.EMAIL_BCC or None,
        connection=backend,
    )
    email.attach_alternative(html_message, "text/html")

    invoice_id = payload.get("invoice_id")
    if invoice_id:
        try:
            from ...invoice.models import Invoice

            invoice = Invoice.objects.get(pk=invoice_id)
            invoice_number = payload.get("invoice_number")
            filename = (
                f"invoice-{invoice_number}.pdf" if invoice_number else "invoice.pdf"
            )
            if invoice.invoice_file:
                pdf_bytes = invoice.invoice_file.read()
                email.attach(filename, pdf_bytes, "application/pdf")
            elif invoice.external_url:
                response = HTTPClient.send_request("GET", invoice.external_url)
                response.raise_for_status()
                email.attach(filename, response.content, "application/pdf")
        except Exception:
            logger.warning(
                "Failed to attach invoice PDF for invoice %s", invoice_id, exc_info=True
            )

    email.send()

    with allow_writer():
        order_events.event_fulfillment_confirmed_notification(
            order_id=from_global_id_or_none(payload["order"]["id"]),
            user_id=from_global_id_or_none(payload["requester_user_id"]),
            app_id=from_global_id_or_none(payload["requester_app_id"]),
            customer_email=recipient_email,
        )

        if payload.get("digital_lines"):
            order_events.event_fulfillment_digital_links_notification(
                order_id=from_global_id_or_none(payload["order"]["id"]),
                user_id=from_global_id_or_none(payload["requester_user_id"]),
                app_id=from_global_id_or_none(payload["requester_app_id"]),
                customer_email=recipient_email,
            )


@app.task(compression="zlib")
def send_fulfillment_update_email_task(
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


@app.task(compression="zlib")
def send_payment_confirmation_email_task(
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
    with allow_writer():
        order_events.event_payment_confirmed_notification(
            order_id=from_global_id_or_none(payload["order"]["id"]),
            user_id=from_global_id_or_none(payload["order"].get("user_id")),
            customer_email=recipient_email,
        )


@app.task(compression="zlib")
def send_order_canceled_email_task(recipient_email, payload, config, subject, template):
    email_config = EmailConfig(**config)
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=template,
    )
    with allow_writer():
        order_events.event_order_cancelled_notification(
            order_id=from_global_id_or_none(payload["order"]["id"]),
            user_id=from_global_id_or_none(payload["requester_user_id"]),
            app_id=from_global_id_or_none(payload["requester_app_id"]),
            customer_email=recipient_email,
        )


@app.task(compression="zlib")
def send_order_refund_email_task(recipient_email, payload, config, subject, template):
    email_config = EmailConfig(**config)
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=template,
    )
    with allow_writer():
        order_events.event_order_refunded_notification(
            order_id=from_global_id_or_none(payload["order"]["id"]),
            user_id=from_global_id_or_none(payload["requester_user_id"]),
            app_id=from_global_id_or_none(payload["requester_app_id"]),
            customer_email=recipient_email,
        )


@app.task(compression="zlib")
def send_order_confirmed_email_task(
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
    with allow_writer():
        order_events.event_order_confirmed_notification(
            order_id=from_global_id_or_none(payload.get("order", {}).get("id")),
            user_id=from_global_id_or_none(payload.get("requester_user_id")),
            app_id=from_global_id_or_none(payload["requester_app_id"]),
            customer_email=recipient_email,
        )


@app.task(compression="zlib")
def send_proforma_fulfillment_confirmation_email_task(
    recipient_email, payload, config, subject, template, quote_pdf_url, quote_number
):
    email_config = EmailConfig(**config)

    compiler = pybars.Compiler()
    helpers = {
        "format_address": format_address,
        "price": price,
        "format_datetime": format_datetime,
        "get_product_image_thumbnail": get_product_image_thumbnail,
        "compare": compare,
    }
    html_message = str(compiler.compile(template)(payload, helpers=helpers))
    subject_message = str(compiler.compile(subject)(payload, helpers))
    plain_text = get_plain_text_message_for_email(html_message)

    from_email = str(
        Address(email_config.sender_name or "", addr_spec=email_config.sender_address)
    )
    backend = EmailBackend(
        host=email_config.host,
        port=email_config.port,
        username=email_config.username,
        password=email_config.password,
        use_ssl=email_config.use_ssl,
        use_tls=email_config.use_tls,
        timeout=DEFAULT_EMAIL_TIMEOUT,
    )

    email = EmailMultiAlternatives(
        subject=subject_message,
        body=plain_text,
        from_email=from_email,
        to=[recipient_email],
        bcc=settings.EMAIL_BCC or None,
        connection=backend,
    )
    email.attach_alternative(html_message, "text/html")

    if quote_pdf_url:
        try:
            logger.debug("Fetching proforma PDF from %s", quote_pdf_url)
            response = HTTPClient.send_request("GET", quote_pdf_url)
            response.raise_for_status()
            pdf_bytes = response.content
            logger.debug(
                "Fetched proforma PDF: %d bytes (status %s)",
                len(pdf_bytes),
                response.status_code,
            )
            filename = f"quote-{quote_number}.pdf" if quote_number else "proforma.pdf"
            email.attach(filename, pdf_bytes, "application/pdf")
            logger.debug("Attached PDF as %s", filename)
        except Exception:
            logger.warning(
                "Failed to fetch proforma PDF from %s", quote_pdf_url, exc_info=True
            )
    else:
        logger.debug("No quote_pdf_url set, skipping PDF attachment")

    email.send()

    with allow_writer():
        order_events.event_fulfillment_confirmed_notification(
            order_id=from_global_id_or_none(payload["order"]["id"]),
            user_id=from_global_id_or_none(payload["requester_user_id"]),
            app_id=from_global_id_or_none(payload["requester_app_id"]),
            customer_email=recipient_email,
        )
