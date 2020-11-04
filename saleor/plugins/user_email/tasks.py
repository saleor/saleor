from urllib.parse import urlencode

from templated_email import send_templated_mail

from ...account import events as account_events
from ...celeryconf import app
from ...core.emails import get_email_context
from ...core.utils.url import prepare_url


@app.task
def send_account_confirmation_email_task(email, token, redirect_url):
    params = urlencode({"email": email, "token": token})
    confirm_url = prepare_url(params, redirect_url)
    send_kwargs, ctx = get_email_context()
    ctx["confirm_url"] = confirm_url
    send_templated_mail(
        template_name="account/confirm",
        recipient_list=[email],
        context=ctx,
        **send_kwargs,
    )


@app.task
def send_password_reset_email_task(recipient_email, redirect_url, user_id, token):
    params = urlencode({"email": recipient_email, "token": token})
    reset_url = prepare_url(params, redirect_url)
    _send_password_reset_email(recipient_email, reset_url, user_id)


def _send_password_reset_email(recipient_email, reset_url, user_id):
    send_kwargs, ctx = get_email_context()
    ctx["reset_url"] = reset_url
    send_templated_mail(
        template_name="account/password_reset",
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )
    account_events.customer_password_reset_link_sent_event(user_id=user_id)


@app.task
def send_request_email_change_email_task(
    new_email, old_email, redirect_url, user_id, token
):
    params = urlencode({"token": token})
    redirect_url = prepare_url(params, redirect_url)
    send_kwargs, ctx = get_email_context()
    ctx["redirect_url"] = redirect_url
    send_templated_mail(
        template_name="account/request_email_change",
        recipient_list=[new_email],
        context=ctx,
        **send_kwargs,
    )
    account_events.customer_email_change_request_event(
        user_id=user_id, parameters={"old_email": old_email, "new_email": new_email}
    )


@app.task
def send_user_change_email_notification_task(recipient_email):
    send_kwargs, ctx = get_email_context()
    send_templated_mail(
        template_name="account/email_changed_notification",
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )


@app.task
def send_account_delete_confirmation_email_task(recipient_email, redirect_url, token):
    params = urlencode({"token": token})
    delete_url = prepare_url(params, redirect_url)
    _send_delete_confirmation_email(recipient_email, delete_url)


def _send_delete_confirmation_email(recipient_email, delete_url):
    send_kwargs, ctx = get_email_context()
    ctx["delete_url"] = delete_url
    send_templated_mail(
        template_name="account/account_delete",
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )


@app.task
def send_set_user_password_email_task(recipient_email, redirect_url, token):
    params = urlencode({"email": recipient_email, "token": token})
    password_set_url = prepare_url(params, redirect_url)
    _send_set_password_email(recipient_email, password_set_url)


def _send_set_password_email(recipient_email, password_set_url):
    send_kwargs, ctx = get_email_context()
    ctx["password_set_url"] = password_set_url
    send_templated_mail(
        template_name="dashboard/customer/set_password",
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )


@app.task
def send_invoice_email_task(recipient_email, invoice_number, invoice_download_url):
    """Send an invoice to user of related order with URL to download it."""
    send_kwargs, ctx = get_email_context()
    ctx["number"] = invoice_number
    ctx["download_url"] = invoice_download_url
    send_templated_mail(
        template_name="order/send_invoice",
        recipient_list=[recipient_email],
        context=ctx,
        **send_kwargs,
    )


@app.task
def send_order_confirmation_email_task(payload):
    """Send order confirmation email."""
    recipient_email = payload["recipient_email"]
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    send_templated_mail(
        template_name="order/confirm_order",
        recipient_list=[recipient_email],
        context=payload,
        **send_kwargs,
    )


@app.task
def send_fulfillment_confirmation_email_task(payload):
    recipient_email = payload["recipient_email"]
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    send_templated_mail(
        template_name="order/confirm_fulfillment",
        recipient_list=[recipient_email],
        context=payload,
        **send_kwargs,
    )


@app.task
def send_fulfillment_update_email_task(payload):
    recipient_email = payload["recipient_email"]
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    send_templated_mail(
        template_name="order/update_fulfillment",
        recipient_list=[recipient_email],
        context=payload,
        **send_kwargs,
    )


@app.task
def send_payment_confirmation_email_task(payload):
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    send_templated_mail(
        template_name="order/payment/confirm_payment",
        recipient_list=[payload["email"]],
        context=payload,
        **send_kwargs,
    )


@app.task
def send_order_canceled_email_task(payload):
    recipient_email = payload["recipient_email"]
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    send_templated_mail(
        template_name="order/order_cancel",
        recipient_list=[recipient_email],
        context=payload,
        **send_kwargs,
    )


@app.task
def send_order_refund_email_task(payload):
    recipient_email = payload["recipient_email"]
    send_kwargs, ctx = get_email_context()
    payload.update(ctx)
    send_templated_mail(
        template_name="order/order_refund",
        recipient_list=[recipient_email],
        context=payload,
        **send_kwargs,
    )
