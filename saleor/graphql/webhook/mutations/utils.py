from typing import cast

import graphene
from django.core.exceptions import ValidationError

from ....app.models import App
from ....webhook.error_codes import WebhookErrorCode
from ...core.validators import validate_one_of_args_is_in_mutation


def get_webhook_object_id(
    *, app: App | None, object_id: str | None, identifier: str | None
) -> str:
    """Resolve a webhook pointer (`id` or `identifier`) to a global ID.

    `identifier` is accepted only from an app referencing its own webhook, and a falsy
    one counts as not provided. See
    `docs/adr/0008-webhook-identifier-is-an-app-only-pointer.md`.
    """
    validate_one_of_args_is_in_mutation("id", object_id, "identifier", identifier)
    if not identifier:
        # the validation above guarantees `object_id` is set
        return cast(str, object_id)
    if app is None:
        raise ValidationError(
            {
                "identifier": ValidationError(
                    "Webhook identifier can only be used by an app to reference its "
                    "own webhook. Use `id` instead.",
                    code=WebhookErrorCode.INVALID.value,
                )
            }
        )
    webhook_pk = (
        app.webhooks.filter(identifier=identifier).values_list("pk", flat=True).first()
    )
    if webhook_pk is None:
        raise ValidationError(
            {
                "identifier": ValidationError(
                    f"Couldn't resolve to a node: {identifier}",
                    code=WebhookErrorCode.NOT_FOUND.value,
                )
            }
        )
    return graphene.Node.to_global_id("Webhook", webhook_pk)
