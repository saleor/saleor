from typing import cast
from urllib.parse import urlencode

from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone

from ..celeryconf import app
from ..core.db.connection import allow_writer
from ..core.utils.events import call_event
from ..core.utils.url import prepare_url
from ..graphql.plugins.dataloaders import get_plugin_manager_promise
from ..graphql.site.dataloaders import get_site_promise
from . import events, notifications, search
from .models import User
from .notifications import send_password_reset_notification
from .utils import RequestorAwareContext


def _prepare_redirect_url(user: User, redirect_url: str, token: str) -> str:
    params = urlencode({"email": user.email, "token": token})
    return prepare_url(params, redirect_url)


@app.task()
@allow_writer()
def trigger_send_password_reset_notification(
    redirect_url, user_pk, context_data, channel_slug
):
    if not user_pk:
        return

    user = User.objects.filter(pk=user_pk).first()
    user = cast(User, user)

    context_data["allow_replica"] = True
    manager = get_plugin_manager_promise(
        RequestorAwareContext.from_context_data(context_data)
    ).get()

    send_password_reset_notification(
        redirect_url=redirect_url,
        user=user,
        manager=manager,
        channel_slug=channel_slug,
        staff=user.is_staff,
    )

    token = default_token_generator.make_token(user)
    redirect_params = _prepare_redirect_url(user, redirect_url, token)

    if user.is_staff:
        call_event(
            manager.staff_set_password_requested,
            user,
            channel_slug,
            token,
            redirect_params,
        )
    else:
        call_event(
            manager.account_set_password_requested,
            user,
            channel_slug,
            token,
            redirect_params,
        )

    user.last_password_reset_request = timezone.now()
    user.save(update_fields=("last_password_reset_request",))


@app.task()
@allow_writer()
def finish_creating_user(user_pk, redirect_url, channel_slug, context_data):
    if not user_pk:
        return

    user = User.objects.get(pk=user_pk)
    user.search_document = search.prepare_user_search_document_value(
        user, attach_addresses_data=False
    )
    user.save(update_fields=["search_document"])

    context_data["allow_replica"] = True
    context = RequestorAwareContext.from_context_data(context_data)

    manager = get_plugin_manager_promise(context).get()
    site = get_site_promise(context).get()

    if site.settings.enable_account_confirmation_by_email:
        # Notifications will be deprecated in the future
        token = default_token_generator.make_token(user)
        notifications.send_account_confirmation(
            user=user,
            redirect_url=redirect_url,
            channel_slug=channel_slug,
            manager=manager,
            token=token,
        )

        if redirect_url:
            redirect_url = _prepare_redirect_url(user, redirect_url, token)

        call_event(
            manager.account_confirmation_requested,
            user,
            channel_slug,
            token,
            redirect_url,
        )

    call_event(manager.customer_created, user)
    events.customer_account_created_event(user=user)
