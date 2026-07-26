from typing import cast

import graphene
from django.core.exceptions import ValidationError

from ....app import models
from ....app.error_codes import AppErrorCode
from ....app.installation_utils import (
    canonicalize_manifest_json,
    resync_app_from_manifest,
    serialize_app_as_manifest,
    serialize_manifest_for_preview,
)
from ....app.manifest_validations import clean_manifest_data
from ....app.types import AppType
from ....permission.enums import AppPermission
from ....webhook.event_types import WebhookEventAsyncType
from ...core.descriptions import ADDED_IN_324
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.fields import JSONString
from ...core.mutations import BaseMutation
from ...core.types import AppError, BaseObjectType
from ...core.utils import WebhookEventInfo
from ...decorators import staff_member_required
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils import get_user_or_app_from_context
from ..types import App
from ..utils import ensure_can_manage_permissions, validate_app_is_not_removed
from .app_fetch_manifest import AppFetchManifest


class AppManifestReloadPreview(BaseObjectType):
    current_manifest = JSONString(
        required=True,
        description=(
            "The installed app's current state, serialized in the manifest shape. "
            "Covers only the fields a reload applies."
        ),
    )
    incoming_manifest = JSONString(
        required=True,
        description=(
            "The freshly fetched manifest, serialized in the same shape as "
            "`currentManifest`."
        ),
    )

    class Meta:
        description = (
            "Preview of the changes a manifest reload would apply." + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_APPS


class AppReloadManifest(BaseMutation):
    app = graphene.Field(App, description="App reloaded from its manifest.")
    preview = graphene.Field(
        AppManifestReloadPreview,
        description="Current and incoming manifest, for reviewing the changes.",
    )

    class Arguments:
        id = graphene.ID(description="ID of the app to reload.", required=True)
        dry_run = graphene.Boolean(
            default_value=False,
            description=(
                "If true, fetch and validate the manifest and return the preview "
                "without applying any changes."
            ),
        )
        expected_incoming_manifest = JSONString(
            required=False,
            description=(
                "The `incomingManifest` returned by a prior dry run. When "
                "provided on apply, the mutation refuses to apply if the manifest "
                "fetched now differs from it — so an admin never silently applies "
                "changes the manifest gained since the preview was reviewed."
            ),
        )

    class Meta:
        auto_permission_message = False
        description = (
            "Reload an installed app from its manifest URL: the app's fields, "
            "permissions, extensions and webhooks are updated to match the "
            "manifest. Webhooks are matched by name; a webhook renamed in the "
            "manifest is deleted and recreated. The `isActive` flag of existing "
            "webhooks and of the app itself, and app tokens, are never modified. "
            "Requires the following permissions: AUTHENTICATED_STAFF_USER "
            "and MANAGE_APPS." + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_APPS
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.APP_UPDATED,
                description="An app was reloaded from its manifest.",
            ),
        ]

    @classmethod
    @staff_member_required
    def perform_mutation(cls, _root, info, /, **data):
        app_global_id = data["id"]
        app = cls.get_node_or_error(info, app_global_id, only_type="App", field="id")
        app = cast(models.App, app)
        validate_app_is_not_removed(app, app_global_id, "id")
        if app.type != AppType.THIRDPARTY or not app.manifest_url:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "The app was not installed from a manifest.",
                        code=AppErrorCode.INVALID.value,
                    )
                }
            )

        manifest_data = AppFetchManifest.fetch_manifest(app.manifest_url)
        if app.identifier and manifest_data.get("id") != app.identifier:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "The manifest identifier does not match the installed app.",
                        code=AppErrorCode.INVALID.value,
                    )
                }
            )
        clean_manifest_data(
            manifest_data, raise_for_saleor_version=True, exclude_app=app
        )
        requestor = get_user_or_app_from_context(info.context)
        ensure_can_manage_permissions(
            requestor,
            [
                permission.formatted_codename
                for permission in manifest_data["permissions"]
            ],
        )

        incoming_manifest = serialize_manifest_for_preview(manifest_data)

        if data["dry_run"]:
            # The current-state serialization walks the app's webhooks/extensions
            # and is only needed to render the diff, so it is skipped on apply.
            preview = AppManifestReloadPreview(
                current_manifest=canonicalize_manifest_json(
                    serialize_app_as_manifest(app)
                ),
                incoming_manifest=canonicalize_manifest_json(incoming_manifest),
            )
            return cls(app=app, preview=preview, errors=[])

        expected = data.get("expected_incoming_manifest")
        if expected is not None and incoming_manifest != expected:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "The manifest changed since the preview was generated. "
                        "Please review the changes again before applying.",
                        code=AppErrorCode.INVALID.value,
                    )
                }
            )

        resync_app_from_manifest(app, manifest_data)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.app_updated, app)
        return cls(app=app, preview=None, errors=[])
