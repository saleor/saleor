import logging

from sendgrid import SendGridAPIClient, SendGridException
from sendgrid.helpers.mail import Mail

from ...account import events as account_events
from ...celeryconf import app
from ...giftcard import events as gift_card_events
from ...graphql.core.utils import from_global_id_or_none
from ...invoice import events as invoice_events
from ...order import events as order_events
from . import SendgridConfiguration

logger = logging.getLogger(__name__)

CELERY_RETRY_BACKOFF = 60
CELERY_RETRY_MAX = 5


def send_email(configuration: SendgridConfiguration, template_id, payload):
    recipient_email = payload["recipient_email"]
    sendgrid_client = SendGridAPIClient(configuration.api_key)
    from_email = (configuration.sender_address, configuration.sender_name)
    message = Mail(from_email=from_email, to_emails=recipient_email)
    message.dynamic_template_data = payload
    message.template_id = template_id
    sendgrid_client.send(message)


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_account_confirmation_email_task(payload: dict, configuration: dict):
    configuration = SendgridConfiguration(**configuration)
    send_email(
        configuration=configuration,
        template_id=configuration.account_confirmation_template_id,
        payload=payload,
    )


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_password_reset_email_task(payload: dict, configuration: dict):
    configuration = SendgridConfiguration(**configuration)
    user_id = payload.get("user", {}).get("id")

    user_id = from_global_id_or_none(user_id)
    send_email(
        configuration=configuration,
        template_id=configuration.account_password_reset_template_id,
        payload=payload,
    )
    account_events.customer_password_reset_link_sent_event(user_id=user_id)


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_request_email_change_email_task(payload: dict, configuration: dict):
    configuration = SendgridConfiguration(**configuration)
    user_id = payload.get("user", {}).get("id")
    send_email(
        configuration=configuration,
        template_id=configuration.account_change_email_request_template_id,
        payload=payload,
    )
    account_events.customer_email_change_request_event(
        user_id=from_global_id_or_none(user_id),
        parameters={
            "old_email": payload.get("old_email"),
            "new_email": payload["recipient_email"],
        },
    )


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_user_change_email_notification_task(payload: dict, configuration: dict):
    configuration = SendgridConfiguration(**configuration)
    user_id = payload.get("user", {}).get("id")
    send_email(
        configuration=configuration,
        template_id=configuration.account_change_email_confirm_template_id,
        payload=payload,
    )
    event_parameters = {
        "old_email": payload["old_email"],
        "new_email": payload["new_email"],
    }

    account_events.customer_email_changed_event(
        user_id=from_global_id_or_none(user_id), parameters=event_parameters
    )


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_account_delete_confirmation_email_task(payload: dict, configuration: dict):
    configuration = SendgridConfiguration(**configuration)
    send_email(
        configuration=configuration,
        template_id=configuration.account_delete_template_id,
        payload=payload,
    )


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_set_user_password_email_task(payload: dict, configuration: dict):
    configuration = SendgridConfiguration(**configuration)
    send_email(
        configuration=configuration,
        template_id=configuration.account_set_customer_password_template_id,
        payload=payload,
    )


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_invoice_email_task(payload: dict, configuration: dict):
    """Send an invoice to user of related order with URL to download it."""
    configuration = SendgridConfiguration(**configuration)
    send_email(
        configuration=configuration,
        template_id=configuration.invoice_ready_template_id,
        payload=payload,
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


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_order_confirmation_email_task(payload: dict, configuration: dict):
    """Send order confirmation email."""
    configuration = SendgridConfiguration(**configuration)
    send_email(
        configuration=configuration,
        template_id=configuration.order_confirmation_template_id,
        payload=payload,
    )
    order_events.event_order_confirmation_notification(
        order_id=from_global_id_or_none(payload["order"]["id"]),
        user_id=from_global_id_or_none(payload["order"].get("user_id")),
        customer_email=payload["recipient_email"],
    )


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_fulfillment_confirmation_email_task(payload: dict, configuration: dict):
    configuration = SendgridConfiguration(**configuration)
    send_email(
        configuration=configuration,
        template_id=configuration.order_fulfillment_confirmation_template_id,
        payload=payload,
    )
    order_events.event_fulfillment_confirmed_notification(
        order_id=from_global_id_or_none(payload["order"]["id"]),
        user_id=from_global_id_or_none(payload["requester_user_id"]),
        app_id=from_global_id_or_none(payload["requester_app_id"]),
        customer_email=payload["recipient_email"],
    )

    if payload.get("digital_lines"):
        order_events.event_fulfillment_digital_links_notification(
            order_id=from_global_id_or_none(payload["order"]["id"]),
            user_id=from_global_id_or_none(payload["requester_user_id"]),
            app_id=from_global_id_or_none(payload["requester_app_id"]),
            customer_email=payload["recipient_email"],
        )


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_fulfillment_update_email_task(payload: dict, configuration: dict):
    configuration = SendgridConfiguration(**configuration)
    send_email(
        configuration=configuration,
        template_id=configuration.order_fulfillment_update_template_id,
        payload=payload,
    )


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_payment_confirmation_email_task(payload: dict, configuration: dict):
    configuration = SendgridConfiguration(**configuration)
    send_email(
        configuration=configuration,
        template_id=configuration.order_payment_confirmation_template_id,
        payload=payload,
    )
    order_events.event_payment_confirmed_notification(
        order_id=from_global_id_or_none(payload["order"]["id"]),
        user_id=from_global_id_or_none(payload["order"].get("user_id")),
        customer_email=payload["recipient_email"],
    )


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_order_canceled_email_task(payload: dict, configuration: dict):
    configuration = SendgridConfiguration(**configuration)
    send_email(
        configuration=configuration,
        template_id=configuration.order_canceled_template_id,
        payload=payload,
    )
    order_events.event_order_cancelled_notification(
        order_id=from_global_id_or_none(payload["order"]["id"]),
        user_id=from_global_id_or_none(payload["requester_user_id"]),
        app_id=from_global_id_or_none(payload["requester_app_id"]),
        customer_email=payload["recipient_email"],
    )


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_order_refund_email_task(payload: dict, configuration: dict):
    configuration = SendgridConfiguration(**configuration)
    send_email(
        configuration=configuration,
        template_id=configuration.order_refund_confirmation_template_id,
        payload=payload,
    )
    order_events.event_order_refunded_notification(
        order_id=from_global_id_or_none(payload["order"]["id"]),
        user_id=from_global_id_or_none(payload["requester_user_id"]),
        app_id=from_global_id_or_none(payload["requester_app_id"]),
        customer_email=payload["recipient_email"],
    )


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_gift_card_email_task(payload: dict, configuration: dict):
    configuration = SendgridConfiguration(**configuration)
    send_email(
        configuration=configuration,
        template_id=configuration.send_gift_card_template_id,
        payload=payload,
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


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_order_confirmed_email_task(payload: dict, configuration: dict):
    configuration = SendgridConfiguration(**configuration)
    send_email(
        configuration=configuration,
        template_id=configuration.order_confirmed_template_id,
        payload=payload,
    )
    order_events.event_order_confirmed_notification(
        order_id=from_global_id_or_none(payload.get("order", {}).get("id")),
        user_id=from_global_id_or_none(payload.get("requester_user_id")),
        app_id=from_global_id_or_none(payload["requester_app_id"]),
        customer_email=payload["recipient_email"],
    )


@app.task(
    autoretry_for=(SendGridException,),
    retry_backoff=CELERY_RETRY_BACKOFF,
    retry_kwargs={"max_retries": CELERY_RETRY_MAX},
    compression="zlib",
)
def send_email_with_dynamic_template_id(
    payload: dict, template_id: str, configuration: dict
):
    configuration = SendgridConfiguration(**configuration)
    send_email(
        configuration=configuration,
        template_id=template_id,
        payload=payload,
    )
