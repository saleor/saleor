from typing import Optional

from ...account import events as account_events
from ...celeryconf import app
from ...invoice import events as invoice_events
from ...order import events as order_events
from ..email_common import (
    EmailConfig,
    get_email_subject,
    get_email_template_or_default,
    send_email,
)
from ..models import PluginConfiguration
from . import constants


def get_plugin_configuration() -> Optional[PluginConfiguration]:
    return PluginConfiguration.objects.filter(identifier=constants.PLUGIN_ID).first()


@app.task(compression="zlib")
def send_account_confirmation_email_task(recipient_email, payload, config):
    email_config = EmailConfig(**config)

    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.ACCOUNT_CONFIRMATION_TEMPLATE_FIELD,
        constants.ACCOUNT_CONFIRMATION_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    subject = get_email_subject(
        plugin_configuration,
        constants.ACCOUNT_CONFIRMATION_SUBJECT_FIELD,
        constants.ACCOUNT_CONFIRMATION_DEFAULT_SUBJECT,
    )

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )


@app.task(compression="zlib")
def send_password_reset_email_task(recipient_email, payload, config):
    user_id = payload.get("user", {}).get("id")
    email_config = EmailConfig(**config)

    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.ACCOUNT_PASSWORD_RESET_TEMPLATE_FIELD,
        constants.ACCOUNT_PASSWORD_RESET_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )

    subject = get_email_subject(
        plugin_configuration,
        constants.ACCOUNT_PASSWORD_RESET_SUBJECT_FIELD,
        constants.ACCOUNT_PASSWORD_RESET_DEFAULT_SUBJECT,
    )
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )
    account_events.customer_password_reset_link_sent_event(user_id=user_id)


@app.task(compression="zlib")
def send_request_email_change_email_task(recipient_email, payload, config):
    user_id = payload.get("user", {}).get("id")
    email_config = EmailConfig(**config)

    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.ACCOUNT_CHANGE_EMAIL_REQUEST_TEMPLATE_FIELD,
        constants.ACCOUNT_CHANGE_EMAIL_REQUEST_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )

    subject = get_email_subject(
        plugin_configuration,
        constants.ACCOUNT_CHANGE_EMAIL_REQUEST_SUBJECT_FIELD,
        constants.ACCOUNT_CHANGE_EMAIL_REQUEST_DEFAULT_SUBJECT,
    )

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )
    account_events.customer_email_change_request_event(
        user_id=user_id,
        parameters={
            "old_email": payload.get("old_email"),
            "new_email": recipient_email,
        },
    )


@app.task(compression="zlib")
def send_user_change_email_notification_task(recipient_email, payload, config):
    user_id = payload.get("user", {}).get("id")
    email_config = EmailConfig(**config)

    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.ACCOUNT_CHANGE_EMAIL_CONFIRM_TEMPLATE_FIELD,
        constants.ACCOUNT_CHANGE_EMAIL_CONFIRM_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )

    subject = get_email_subject(
        plugin_configuration,
        constants.ACCOUNT_CHANGE_EMAIL_CONFIRM_SUBJECT_FIELD,
        constants.ACCOUNT_CHANGE_EMAIL_CONFIRM_DEFAULT_SUBJECT,
    )

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )
    event_parameters = {
        "old_email": payload["old_email"],
        "new_email": payload["new_email"],
    }

    account_events.customer_email_changed_event(
        user_id=user_id, parameters=event_parameters
    )


@app.task(compression="zlib")
def send_account_delete_confirmation_email_task(recipient_email, payload, config):
    email_config = EmailConfig(**config)

    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.ACCOUNT_DELETE_TEMPLATE_FIELD,
        constants.ACCOUNT_DELETE_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )

    subject = get_email_subject(
        plugin_configuration,
        constants.ACCOUNT_DELETE_SUBJECT_FIELD,
        constants.ACCOUNT_DELETE_DEFAULT_SUBJECT,
    )

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )


@app.task(compression="zlib")
def send_set_user_password_email_task(recipient_email, payload, config):
    email_config = EmailConfig(**config)

    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.ACCOUNT_SET_CUSTOMER_PASSWORD_TEMPLATE_FIELD,
        constants.ACCOUNT_SET_CUSTOMER_PASSWORD_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )

    subject = get_email_subject(
        plugin_configuration,
        constants.ACCOUNT_SET_CUSTOMER_PASSWORD_SUBJECT_FIELD,
        constants.ACCOUNT_SET_CUSTOMER_PASSWORD_DEFAULT_SUBJECT,
    )

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )


@app.task(compression="zlib")
def send_invoice_email_task(recipient_email, payload, config):
    """Send an invoice to user of related order with URL to download it."""
    email_config = EmailConfig(**config)

    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.INVOICE_READY_TEMPLATE_FIELD,
        constants.INVOICE_READY_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )

    subject = get_email_subject(
        plugin_configuration,
        constants.INVOICE_READY_SUBJECT_FIELD,
        constants.INVOICE_READY_DEFAULT_SUBJECT,
    )

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )
    invoice_events.notification_invoice_sent_event(
        user_id=payload["requester_user_id"],
        app_id=payload["requester_app_id"],
        invoice_id=payload["invoice"]["id"],
        customer_email=payload["recipient_email"],
    )
    order_events.event_invoice_sent_notification(
        order_id=payload["invoice"]["order_id"],
        user_id=payload["requester_user_id"],
        app_id=payload["requester_app_id"],
        email=payload["recipient_email"],
    )


@app.task(compression="zlib")
def send_order_confirmation_email_task(recipient_email, payload, config):
    """Send order confirmation email."""
    email_config = EmailConfig(**config)

    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.ORDER_CONFIRMATION_TEMPLATE_FIELD,
        constants.ORDER_CONFIRMATION_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )

    subject = get_email_subject(
        plugin_configuration,
        constants.ORDER_CONFIRMATION_SUBJECT_FIELD,
        constants.ORDER_CONFIRMATION_DEFAULT_SUBJECT,
    )

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )
    order_events.event_order_confirmation_notification(
        order_id=payload["order"]["id"],
        user_id=payload["order"].get("user_id"),
        customer_email=recipient_email,
    )


@app.task(compression="zlib")
def send_fulfillment_confirmation_email_task(recipient_email, payload, config):
    email_config = EmailConfig(**config)

    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.ORDER_FULFILLMENT_CONFIRMATION_TEMPLATE_FIELD,
        constants.ORDER_FULFILLMENT_CONFIRMATION_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )

    subject = get_email_subject(
        plugin_configuration,
        constants.ORDER_FULFILLMENT_CONFIRMATION_SUBJECT_FIELD,
        constants.ORDER_FULFILLMENT_CONFIRMATION_DEFAULT_SUBJECT,
    )

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )
    order_events.event_fulfillment_confirmed_notification(
        order_id=payload["order"]["id"],
        user_id=payload["requester_user_id"],
        app_id=payload["requester_app_id"],
        customer_email=recipient_email,
    )

    if payload.get("digital_lines"):
        order_events.event_fulfillment_digital_links_notification(
            order_id=payload["order"]["id"],
            user_id=payload["requester_user_id"],
            app_id=payload["requester_app_id"],
            customer_email=recipient_email,
        )


@app.task(compression="zlib")
def send_fulfillment_update_email_task(recipient_email, payload, config):
    email_config = EmailConfig(**config)
    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.ORDER_FULFILLMENT_UPDATE_TEMPLATE_FIELD,
        constants.ORDER_FULFILLMENT_UPDATE_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )

    subject = get_email_subject(
        plugin_configuration,
        constants.ORDER_FULFILLMENT_UPDATE_SUBJECT_FIELD,
        constants.ORDER_FULFILLMENT_UPDATE_DEFAULT_SUBJECT,
    )
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )


@app.task(compression="zlib")
def send_payment_confirmation_email_task(recipient_email, payload, config):
    email_config = EmailConfig(**config)

    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.ORDER_PAYMENT_CONFIRMATION_TEMPLATE_FIELD,
        constants.ORDER_PAYMENT_CONFIRMATION_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )

    subject = get_email_subject(
        plugin_configuration,
        constants.ORDER_PAYMENT_CONFIRMATION_SUBJECT_FIELD,
        constants.ORDER_PAYMENT_CONFIRMATION_DEFAULT_SUBJECT,
    )

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )
    order_events.event_payment_confirmed_notification(
        order_id=payload["order"]["id"],
        user_id=payload["order"].get("user_id"),
        customer_email=recipient_email,
    )


@app.task(compression="zlib")
def send_order_canceled_email_task(recipient_email, payload, config):
    email_config = EmailConfig(**config)

    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.ORDER_CANCELED_TEMPLATE_FIELD,
        constants.ORDER_CANCELED_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )

    subject = get_email_subject(
        plugin_configuration,
        constants.ORDER_CANCELED_SUBJECT_FIELD,
        constants.ORDER_CANCELED_DEFAULT_SUBJECT,
    )

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )
    order_events.event_order_cancelled_notification(
        order_id=payload["order"]["id"],
        user_id=payload["requester_user_id"],
        app_id=payload["requester_app_id"],
        customer_email=recipient_email,
    )


@app.task(compression="zlib")
def send_order_refund_email_task(recipient_email, payload, config):
    email_config = EmailConfig(**config)

    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.ORDER_REFUND_CONFIRMATION_TEMPLATE_FIELD,
        constants.ORDER_REFUND_CONFIRMATION_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )

    subject = get_email_subject(
        plugin_configuration,
        constants.ORDER_REFUND_CONFIRMATION_SUBJECT_FIELD,
        constants.ORDER_REFUND_CONFIRMATION_DEFAULT_SUBJECT,
    )

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )
    order_events.event_order_refunded_notification(
        order_id=payload["order"]["id"],
        user_id=payload["requester_user_id"],
        app_id=payload["requester_app_id"],
        customer_email=recipient_email,
    )


@app.task(compression="zlib")
def send_order_confirmed_email_task(recipient_email, payload, config):
    email_config = EmailConfig(**config)

    plugin_configuration = get_plugin_configuration()
    email_template_str = get_email_template_or_default(
        plugin_configuration,
        constants.ORDER_CONFIRMED_TEMPLATE_FIELD,
        constants.ORDER_CONFIRMED_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )

    subject = get_email_subject(
        plugin_configuration,
        constants.ORDER_CONFIRMED_SUBJECT_FIELD,
        constants.ORDER_CONFIRMED_DEFAULT_SUBJECT,
    )

    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=subject,
        template_str=email_template_str,
    )
    order_events.event_order_confirmed_notification(
        order_id=payload.get("order", {}).get("id"),
        user_id=payload.get("requester_user_id"),
        app_id=payload["requester_app_id"],
        customer_email=recipient_email,
    )
