import pytest
from django.db import IntegrityError
from django.db.transaction import atomic

from ...app.models import App
from ..models import Webhook

TARGET_URL = "http://www.example.com/test"


def test_webhook_identifier_must_be_unique_per_app(app):
    # given
    identifier = "order-created-handler"
    Webhook.objects.create(app=app, target_url=TARGET_URL, identifier=identifier)

    # when / then - reusing the identifier within the same app is rejected
    with pytest.raises(IntegrityError), atomic():
        Webhook.objects.create(app=app, target_url=TARGET_URL, identifier=identifier)


def test_webhook_identifier_can_be_reused_across_apps(app):
    # given
    identifier = "order-created-handler"
    other_app = App.objects.create(name="Other app")
    Webhook.objects.create(app=app, target_url=TARGET_URL, identifier=identifier)

    # when - a different app uses the same identifier
    webhook = Webhook.objects.create(
        app=other_app, target_url=TARGET_URL, identifier=identifier
    )

    # then
    assert webhook.identifier == identifier


def test_webhook_allows_multiple_null_identifiers_per_app(app):
    # given / when - two webhooks of the same app omit the identifier
    first = Webhook.objects.create(app=app, target_url=TARGET_URL)
    second = Webhook.objects.create(app=app, target_url=TARGET_URL)

    # then - NULL identifiers are exempt from the uniqueness constraint
    assert first.identifier is None
    assert second.identifier is None


def test_webhook_identifier_cannot_be_blank(app):
    # given / when / then - a blank identifier is rejected at the database level
    with pytest.raises(IntegrityError), atomic():
        Webhook.objects.create(app=app, target_url=TARGET_URL, identifier="")
