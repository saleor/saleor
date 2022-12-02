from ...account import events as account_events
from ...celeryconf import app
from ...giftcard import events as gift_card_events
from ...graphql.core.utils import from_global_id_or_none
from ...invoice import events as invoice_events
from ...order import events as order_events
from ..email_common import EmailConfig, send_email


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
        "old_email": payload["old_email"],
        "new_email": payload["new_email"],
    }

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

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=template,
    )
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
    order_events.event_order_confirmed_notification(
        order_id=from_global_id_or_none(payload.get("order", {}).get("id")),
        user_id=from_global_id_or_none(payload.get("requester_user_id")),
        app_id=from_global_id_or_none(payload["requester_app_id"]),
        customer_email=recipient_email,
    )
