from urllib.parse import urlencode

from ...account import events as account_events
from ...celeryconf import app
from ...core.emails import get_email_context
from ...core.utils.url import prepare_url
from ..email_common import EmailConfig, send_email


@app.task
def send_account_confirmation_email_task(email, token, redirect_url, config):
    email_config = EmailConfig(**config)
    params = urlencode({"email": email, "token": token})
    confirm_url = prepare_url(params, redirect_url)
    send_kwargs, ctx = get_email_context()
    ctx["confirm_url"] = confirm_url
    send_email(
        config=email_config,
        recipient_list=[email],
        template_name="account/confirm",
        context=ctx,
    )


@app.task
def send_password_reset_email_task(
    recipient_email, redirect_url, user_id, token, config
):
    email_config = EmailConfig(**config)
    params = urlencode({"email": recipient_email, "token": token})
    reset_url = prepare_url(params, redirect_url)
    _send_password_reset_email(recipient_email, reset_url, user_id, email_config)


def _send_password_reset_email(recipient_email, reset_url, user_id, email_config):
    send_kwargs, ctx = get_email_context()
    ctx["reset_url"] = reset_url
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        template_name="account/password_reset",
        context=ctx,
    )
    account_events.customer_password_reset_link_sent_event(user_id=user_id)


@app.task
def send_request_email_change_email_task(
    new_email, old_email, redirect_url, user_id, token, config
):
    email_config = EmailConfig(**config)
    params = urlencode({"token": token})
    redirect_url = prepare_url(params, redirect_url)
    send_kwargs, ctx = get_email_context()
    ctx["redirect_url"] = redirect_url
    send_email(
        config=email_config,
        recipient_list=[new_email],
        template_name="account/request_email_change",
        context=ctx,
    )
    account_events.customer_email_change_request_event(
        user_id=user_id, parameters={"old_email": old_email, "new_email": new_email}
    )


@app.task
def send_user_change_email_notification_task(recipient_email, config):
    email_config = EmailConfig(**config)
    send_kwargs, ctx = get_email_context()
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        template_name="account/email_changed_notification",
        context=ctx,
    )


@app.task
def send_account_delete_confirmation_email_task(
    recipient_email, redirect_url, token, config
):
    email_config = EmailConfig(**config)
    params = urlencode({"token": token})
    delete_url = prepare_url(params, redirect_url)
    _send_delete_confirmation_email(recipient_email, delete_url, email_config)


def _send_delete_confirmation_email(recipient_email, delete_url, email_config):
    send_kwargs, ctx = get_email_context()
    ctx["delete_url"] = delete_url
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        template_name="account/account_delete",
        context=ctx,
    )


@app.task
def send_set_user_password_email_task(recipient_email, redirect_url, token, config):
    email_config = EmailConfig(**config)
    params = urlencode({"email": recipient_email, "token": token})
    password_set_url = prepare_url(params, redirect_url)
    _send_set_password_email(recipient_email, password_set_url, email_config)


def _send_set_password_email(recipient_email, password_set_url, email_config):
    send_kwargs, ctx = get_email_context()
    ctx["password_set_url"] = password_set_url
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        template_name="dashboard/customer/set_password",
        context=ctx,
    )


@app.task
def send_invoice_email_task(
    recipient_email, invoice_number, invoice_download_url, config
):
    """Send an invoice to user of related order with URL to download it."""
    email_config = EmailConfig(**config)
    send_kwargs, ctx = get_email_context()
    ctx["number"] = invoice_number
    ctx["download_url"] = invoice_download_url
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        template_name="order/send_invoice",
        context=ctx,
    )


@app.task
def send_order_confirmation_email_task(payload, config):
    """Send order confirmation email."""
    email_config = EmailConfig(**config)
    recipient_email = payload["recipient_email"]
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        template_name="order/confirm_fulfillment",
        context=payload,
    )


@app.task
def send_fulfillment_confirmation_email_task(payload, config):
    email_config = EmailConfig(**config)
    recipient_email = payload["recipient_email"]
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        template_name="order/confirm_fulfillment",
        context=payload,
    )


@app.task
def send_fulfillment_update_email_task(payload, config):
    email_config = EmailConfig(**config)
    recipient_email = payload["recipient_email"]
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        template_name="order/update_fulfillment",
        context=payload,
    )


@app.task
def send_payment_confirmation_email_task(payload, config):
    email_config = EmailConfig(**config)
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    recipient_email = payload["recipient_email"]
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        template_name="order/payment/confirm_payment",
        context=payload,
    )


@app.task
def send_order_canceled_email_task(payload, config):
    email_config = EmailConfig(**config)
    recipient_email = payload["recipient_email"]
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        template_name="order/order_cancel",
        context=payload,
    )


@app.task
def send_order_refund_email_task(payload, config):
    email_config = EmailConfig(**config)
    recipient_email = payload["recipient_email"]
    # TODO when we replace template define if this context is required
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    send_email(
        config=email_config,
        recipient_list=[recipient_email],
        template_name="order/order_refund",
        context=payload,
    )
