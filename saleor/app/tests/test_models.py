import pytest
from django.db import IntegrityError
from django.db.transaction import atomic

from ...app.models import App
from ...webhook.event_types import WebhookEventSyncType
from ..models import AppExtension, AppInstallation


def test_qs_for_event_type(payment_app):
    qs = App.objects.for_event_type(WebhookEventSyncType.PAYMENT_AUTHORIZE)
    assert len(qs) == 1
    assert qs[0] == payment_app


def test_qs_for_event_type_no_payment_permissions(payment_app):
    payment_app.permissions.first().delete()
    qs = App.objects.for_event_type(WebhookEventSyncType.PAYMENT_AUTHORIZE)
    assert len(qs) == 0


def test_qs_for_event_type_inactive_app(payment_app):
    payment_app.is_active = False
    payment_app.save()
    qs = App.objects.for_event_type(WebhookEventSyncType.PAYMENT_AUTHORIZE)
    assert len(qs) == 0


def test_qs_for_event_type_no_webhook_event(payment_app):
    webhook = payment_app.webhooks.first()
    event = webhook.events.filter(
        event_type=WebhookEventSyncType.PAYMENT_AUTHORIZE
    ).first()
    event.delete()
    qs = App.objects.for_event_type(WebhookEventSyncType.PAYMENT_AUTHORIZE)
    assert len(qs) == 0


def test_qs_for_event_type_inactive_webhook(payment_app):
    webhook = payment_app.webhooks.first()
    webhook.is_active = False
    webhook.save()
    qs = App.objects.for_event_type(WebhookEventSyncType.PAYMENT_AUTHORIZE)
    assert len(qs) == 0


def test_app_extension_identifier_must_be_unique_per_app(app):
    # given
    identifier = "refund-button"
    AppExtension.objects.create(
        app=app,
        label="Extension",
        url="https://example.com/ext",
        mount="product_overview_more_actions",
        identifier=identifier,
    )

    # when / then - reusing the identifier within the same app is rejected
    with pytest.raises(IntegrityError), atomic():
        AppExtension.objects.create(
            app=app,
            label="Other extension",
            url="https://example.com/ext-2",
            mount="product_details_more_actions",
            identifier=identifier,
        )


def test_app_extension_identifier_can_be_reused_across_apps(app):
    # given
    identifier = "refund-button"
    other_app = App.objects.create(name="Other app")
    AppExtension.objects.create(
        app=app,
        label="Extension",
        url="https://example.com/ext",
        mount="product_overview_more_actions",
        identifier=identifier,
    )

    # when - a different app uses the same identifier
    extension = AppExtension.objects.create(
        app=other_app,
        label="Extension",
        url="https://example.com/ext",
        mount="product_overview_more_actions",
        identifier=identifier,
    )

    # then
    assert extension.identifier == identifier


def test_app_extension_allows_multiple_null_identifiers_per_app(app):
    # given / when - two extensions of the same app omit the identifier
    first = AppExtension.objects.create(
        app=app,
        label="Extension",
        url="https://example.com/ext",
        mount="product_overview_more_actions",
    )
    second = AppExtension.objects.create(
        app=app,
        label="Other extension",
        url="https://example.com/ext-2",
        mount="product_details_more_actions",
    )

    # then - NULL identifiers are exempt from the uniqueness constraint
    assert first.identifier is None
    assert second.identifier is None


def test_app_extension_identifier_cannot_be_blank(app):
    # given / when / then - a blank identifier is rejected at the database level
    with pytest.raises(IntegrityError), atomic():
        AppExtension.objects.create(
            app=app,
            label="Extension",
            url="https://example.com/ext",
            mount="product_overview_more_actions",
            identifier="",
        )


def test_app_installation_set_message_truncates(app_installation):
    max_length = AppInstallation._meta.get_field("message").max_length
    too_long_message = "msg" * max_length

    app_installation.set_message(too_long_message)
    app_installation.save()
    app_installation.refresh_from_db()

    assert len(app_installation.message) <= max_length
