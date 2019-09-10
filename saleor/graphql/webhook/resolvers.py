from ...webhook.models import Webhook


def resolve_webhooks():
    return Webhook.objects.all()
