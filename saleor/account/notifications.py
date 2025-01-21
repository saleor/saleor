from urllib.parse import urlencode

from django.contrib.auth.tokens import default_token_generator

from ..core.notification.utils import get_site_context
from ..core.notify import NotifyEventType, NotifyHandler
from ..core.tokens import account_delete_token_generator
from ..core.utils.url import prepare_url
from ..graphql.core.utils import to_global_id_or_none
from .models import User


def get_default_user_payload(user: User):
    payload = {
        "id": to_global_id_or_none(user),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
        "is_active": user.is_active,
        "private_metadata": user.private_metadata,
        "metadata": user.metadata,
        "language_code": user.language_code,
    }
    # Deprecated: override private_metadata with empty dict as it shouldn't be returned
    # in the payload (see SALEOR-7046). Should be removed in Saleor 4.0.
    payload["private_metadata"] = {}
    return payload


def get_user_custom_payload(user: User):
    payload = {
        "user": get_default_user_payload(user),
        "recipient_email": user.email,
        **get_site_context(),
    }
    return payload


def send_password_reset_notification(
    redirect_url, user, manager, channel_slug: str | None, staff=False
):
    """Trigger sending a password reset notification for the given customer/staff."""

    def _generate_payload():
        token = default_token_generator.make_token(user)
        params = urlencode({"email": user.email, "token": token})
        reset_url = prepare_url(params, redirect_url)

        payload = {
            "user": get_default_user_payload(user),
            "recipient_email": user.email,
            "token": token,
            "reset_url": reset_url,
            "channel_slug": channel_slug,
            **get_site_context(),
        }
        return payload

    event = (
        NotifyEventType.ACCOUNT_STAFF_RESET_PASSWORD
        if staff
        else NotifyEventType.ACCOUNT_PASSWORD_RESET
    )
    handler = NotifyHandler(_generate_payload)
    manager.notify(event, payload_func=handler.payload, channel_slug=channel_slug)


def send_account_confirmation(user, redirect_url, manager, channel_slug, token=None):
    """Trigger sending an account confirmation notification for the given user."""

    def _generate_payload():
        if not token:
            user_token = default_token_generator.make_token(user)
        else:
            user_token = token

        params = urlencode({"email": user.email, "token": user_token})
        confirm_url = prepare_url(params, redirect_url)
        payload = {
            "user": get_default_user_payload(user),
            "recipient_email": user.email,
            "token": user_token,
            "confirm_url": confirm_url,
            "channel_slug": channel_slug,
            **get_site_context(),
        }
        return payload

    handler = NotifyHandler(_generate_payload)
    manager.notify(
        NotifyEventType.ACCOUNT_CONFIRMATION,
        payload_func=handler.payload,
        channel_slug=channel_slug,
    )


def send_request_user_change_email_notification(
    redirect_url, user, new_email, token, manager, channel_slug
):
    """Trigger sending a notification change email for the given user."""

    def _generate_payload():
        params = urlencode({"token": token})
        prepared_redirect_url = prepare_url(params, redirect_url)
        payload = {
            "user": get_default_user_payload(user),
            "recipient_email": new_email,
            "old_email": user.email,
            "new_email": new_email,
            "token": token,
            "redirect_url": prepared_redirect_url,
            "channel_slug": channel_slug,
            **get_site_context(),
        }
        return payload

    handler = NotifyHandler(_generate_payload)
    manager.notify(
        NotifyEventType.ACCOUNT_CHANGE_EMAIL_REQUEST,
        payload_func=handler.payload,
        channel_slug=channel_slug,
    )


def send_user_change_email_notification(recipient_email, user, manager, channel_slug):
    """Trigger sending an email change notification for the given user."""

    def _generate_payload():
        payload = {
            "user": get_default_user_payload(user),
            "recipient_email": recipient_email,
            "channel_slug": channel_slug,
            "old_email": recipient_email,
            "new_email": user.email,
            **get_site_context(),
        }
        return payload

    handler = NotifyHandler(_generate_payload)
    manager.notify(
        NotifyEventType.ACCOUNT_CHANGE_EMAIL_CONFIRM,
        payload_func=handler.payload,
        channel_slug=channel_slug,
    )


def send_account_delete_confirmation_notification(
    redirect_url, user, manager, channel_slug, token=None
):
    """Trigger sending an account delete notification for the given user."""

    def _generate_payload():
        if not token:
            user_token = account_delete_token_generator.make_token(user)
        else:
            user_token = token
        params = urlencode({"token": user_token})
        delete_url = prepare_url(params, redirect_url)
        payload = {
            "user": get_default_user_payload(user),
            "recipient_email": user.email,
            "token": user_token,
            "delete_url": delete_url,
            "channel_slug": channel_slug,
            **get_site_context(),
        }
        return payload

    handler = NotifyHandler(_generate_payload)
    manager.notify(
        NotifyEventType.ACCOUNT_DELETE,
        payload_func=handler.payload,
        channel_slug=channel_slug,
    )


def send_set_password_notification(
    redirect_url, user, manager, channel_slug, staff=False
):
    """Trigger sending a set password notification for the given customer/staff."""

    def _generate_payload():
        token = default_token_generator.make_token(user)
        params = urlencode({"email": user.email, "token": token})
        password_set_url = prepare_url(params, redirect_url)
        payload = {
            "user": get_default_user_payload(user),
            "token": default_token_generator.make_token(user),
            "recipient_email": user.email,
            "password_set_url": password_set_url,
            "channel_slug": channel_slug,
            **get_site_context(),
        }
        return payload

    if staff:
        event = NotifyEventType.ACCOUNT_SET_STAFF_PASSWORD
    else:
        event = NotifyEventType.ACCOUNT_SET_CUSTOMER_PASSWORD
    handler = NotifyHandler(_generate_payload)
    manager.notify(event, payload_func=handler.payload, channel_slug=channel_slug)
