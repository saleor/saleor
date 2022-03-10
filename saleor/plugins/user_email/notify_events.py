from typing import TYPE_CHECKING

from ..email_common import get_email_subject, get_email_template_or_default
from . import constants
from .tasks import (
    send_account_confirmation_email_task,
    send_account_delete_confirmation_email_task,
    send_fulfillment_confirmation_email_task,
    send_fulfillment_update_email_task,
    send_gift_card_email_task,
    send_invoice_email_task,
    send_order_canceled_email_task,
    send_order_confirmation_email_task,
    send_order_confirmed_email_task,
    send_order_refund_email_task,
    send_password_reset_email_task,
    send_payment_confirmation_email_task,
    send_request_email_change_email_task,
    send_set_user_password_email_task,
    send_user_change_email_notification_task,
)

if TYPE_CHECKING:
    from .plugin import UserEmailPlugin


def send_account_password_reset_event(
    payload: dict, config: dict, plugin: "UserEmailPlugin"
):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.ACCOUNT_PASSWORD_RESET_TEMPLATE_FIELD,
        constants.ACCOUNT_PASSWORD_RESET_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return
    subject = get_email_subject(
        plugin.configuration,
        constants.ACCOUNT_PASSWORD_RESET_SUBJECT_FIELD,
        constants.ACCOUNT_PASSWORD_RESET_DEFAULT_SUBJECT,
    )
    send_password_reset_email_task.delay(
        recipient_email,
        payload,
        config,
        subject,
        template,
    )


def send_account_confirmation(payload: dict, config: dict, plugin: "UserEmailPlugin"):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.ACCOUNT_CONFIRMATION_TEMPLATE_FIELD,
        constants.ACCOUNT_CONFIRMATION_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return
    subject = get_email_subject(
        plugin.configuration,
        constants.ACCOUNT_CONFIRMATION_SUBJECT_FIELD,
        constants.ACCOUNT_CONFIRMATION_DEFAULT_SUBJECT,
    )
    send_account_confirmation_email_task.delay(
        recipient_email, payload, config, subject, template
    )


def send_account_change_email_request(
    payload: dict, config: dict, plugin: "UserEmailPlugin"
):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.ACCOUNT_CHANGE_EMAIL_REQUEST_TEMPLATE_FIELD,
        constants.ACCOUNT_CHANGE_EMAIL_REQUEST_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return
    subject = get_email_subject(
        plugin.configuration,
        constants.ACCOUNT_CHANGE_EMAIL_REQUEST_SUBJECT_FIELD,
        constants.ACCOUNT_CHANGE_EMAIL_REQUEST_DEFAULT_SUBJECT,
    )
    send_request_email_change_email_task.delay(
        recipient_email, payload, config, subject, template
    )


def send_account_change_email_confirm(
    payload: dict, config: dict, plugin: "UserEmailPlugin"
):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.ACCOUNT_CHANGE_EMAIL_CONFIRM_TEMPLATE_FIELD,
        constants.ACCOUNT_CHANGE_EMAIL_CONFIRM_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return
    subject = get_email_subject(
        plugin.configuration,
        constants.ACCOUNT_CHANGE_EMAIL_CONFIRM_SUBJECT_FIELD,
        constants.ACCOUNT_CHANGE_EMAIL_CONFIRM_DEFAULT_SUBJECT,
    )
    send_user_change_email_notification_task.delay(
        recipient_email, payload, config, subject, template
    )


def send_account_delete(payload: dict, config: dict, plugin: "UserEmailPlugin"):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.ACCOUNT_DELETE_TEMPLATE_FIELD,
        constants.ACCOUNT_DELETE_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return
    subject = get_email_subject(
        plugin.configuration,
        constants.ACCOUNT_DELETE_SUBJECT_FIELD,
        constants.ACCOUNT_DELETE_DEFAULT_SUBJECT,
    )
    send_account_delete_confirmation_email_task.delay(
        recipient_email, payload, config, subject, template
    )


def send_gift_card(payload: dict, config: dict, plugin: "UserEmailPlugin"):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.SEND_GIFT_CARD_TEMPLATE_FIELD,
        constants.SEND_GIFT_CARD_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return

    subject = get_email_subject(
        plugin.configuration,
        constants.SEND_GIFT_CARD_SUBJECT_FIELD,
        constants.SEND_GIFT_CARD_DEFAULT_SUBJECT,
    )
    send_gift_card_email_task.delay(recipient_email, payload, config, subject, template)


def send_account_set_customer_password(
    payload: dict, config: dict, plugin: "UserEmailPlugin"
):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.ACCOUNT_SET_CUSTOMER_PASSWORD_TEMPLATE_FIELD,
        constants.ACCOUNT_SET_CUSTOMER_PASSWORD_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return
    subject = get_email_subject(
        plugin.configuration,
        constants.ACCOUNT_SET_CUSTOMER_PASSWORD_SUBJECT_FIELD,
        constants.ACCOUNT_SET_CUSTOMER_PASSWORD_DEFAULT_SUBJECT,
    )
    send_set_user_password_email_task.delay(
        recipient_email, payload, config, subject, template
    )


def send_invoice(payload: dict, config: dict, plugin: "UserEmailPlugin"):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.INVOICE_READY_TEMPLATE_FIELD,
        constants.INVOICE_READY_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return
    subject = get_email_subject(
        plugin.configuration,
        constants.INVOICE_READY_SUBJECT_FIELD,
        constants.INVOICE_READY_DEFAULT_SUBJECT,
    )
    send_invoice_email_task.delay(recipient_email, payload, config, subject, template)


def send_order_confirmation(payload: dict, config: dict, plugin: "UserEmailPlugin"):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.ORDER_CONFIRMATION_TEMPLATE_FIELD,
        constants.ORDER_CONFIRMATION_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return
    subject = get_email_subject(
        plugin.configuration,
        constants.ORDER_CONFIRMATION_SUBJECT_FIELD,
        constants.ORDER_CONFIRMATION_DEFAULT_SUBJECT,
    )
    send_order_confirmation_email_task.delay(
        recipient_email, payload, config, subject, template
    )


def send_fulfillment_confirmation(
    payload: dict, config: dict, plugin: "UserEmailPlugin"
):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.ORDER_FULFILLMENT_CONFIRMATION_TEMPLATE_FIELD,
        constants.ORDER_FULFILLMENT_CONFIRMATION_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return
    subject = get_email_subject(
        plugin.configuration,
        constants.ORDER_FULFILLMENT_CONFIRMATION_SUBJECT_FIELD,
        constants.ORDER_FULFILLMENT_CONFIRMATION_DEFAULT_SUBJECT,
    )
    send_fulfillment_confirmation_email_task.delay(
        recipient_email, payload, config, subject, template
    )


def send_fulfillment_update(payload: dict, config: dict, plugin: "UserEmailPlugin"):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.ORDER_FULFILLMENT_UPDATE_TEMPLATE_FIELD,
        constants.ORDER_FULFILLMENT_UPDATE_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return
    subject = get_email_subject(
        plugin.configuration,
        constants.ORDER_FULFILLMENT_UPDATE_SUBJECT_FIELD,
        constants.ORDER_FULFILLMENT_UPDATE_DEFAULT_SUBJECT,
    )
    send_fulfillment_update_email_task.delay(
        recipient_email, payload, config, subject, template
    )


def send_payment_confirmation(payload: dict, config: dict, plugin: "UserEmailPlugin"):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.ORDER_PAYMENT_CONFIRMATION_TEMPLATE_FIELD,
        constants.ORDER_PAYMENT_CONFIRMATION_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return
    subject = get_email_subject(
        plugin.configuration,
        constants.ORDER_PAYMENT_CONFIRMATION_SUBJECT_FIELD,
        constants.ORDER_PAYMENT_CONFIRMATION_DEFAULT_SUBJECT,
    )
    send_payment_confirmation_email_task.delay(
        recipient_email, payload, config, subject, template
    )


def send_order_canceled(payload: dict, config: dict, plugin: "UserEmailPlugin"):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.ORDER_CANCELED_TEMPLATE_FIELD,
        constants.ORDER_CANCELED_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return
    subject = get_email_subject(
        plugin.configuration,
        constants.ORDER_CANCELED_SUBJECT_FIELD,
        constants.ORDER_CANCELED_DEFAULT_SUBJECT,
    )
    send_order_canceled_email_task.delay(
        recipient_email, payload, config, subject, template
    )


def send_order_refund(payload: dict, config: dict, plugin: "UserEmailPlugin"):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.ORDER_REFUND_CONFIRMATION_TEMPLATE_FIELD,
        constants.ORDER_REFUND_CONFIRMATION_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return
    subject = get_email_subject(
        plugin.configuration,
        constants.ORDER_REFUND_CONFIRMATION_SUBJECT_FIELD,
        constants.ORDER_REFUND_CONFIRMATION_DEFAULT_SUBJECT,
    )
    send_order_refund_email_task.delay(
        recipient_email, payload, config, subject, template
    )


def send_order_confirmed(payload: dict, config: dict, plugin: "UserEmailPlugin"):
    recipient_email = payload["recipient_email"]
    template = get_email_template_or_default(
        plugin,
        constants.ORDER_CONFIRMED_TEMPLATE_FIELD,
        constants.ORDER_CONFIRMED_DEFAULT_TEMPLATE,
        constants.DEFAULT_EMAIL_TEMPLATES_PATH,
    )
    if not template:
        # Empty template means that we don't want to trigger a given event.
        return
    subject = get_email_subject(
        plugin.configuration,
        constants.ORDER_CONFIRMED_SUBJECT_FIELD,
        constants.ORDER_CONFIRMED_DEFAULT_SUBJECT,
    )
    send_order_confirmed_email_task.delay(
        recipient_email, payload, config, subject, template
    )
