import logging
import time
from typing import cast

import graphene
from django.core.exceptions import ValidationError

from ....app import models as app_models
from ....app.error_codes import AppErrorCode
from ....graphql.app.enums import CircuitBreakerState
from ....graphql.app.types import App
from ....graphql.core.descriptions import ADDED_IN_321
from ....permission.enums import AppPermission
from ....webhook.circuit_breaker.breaker_board import (
    initialize_breaker_board,
)
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import BaseMutation
from ...core.types import AppError
from ...utils import get_user_or_app_from_context

logger = logging.getLogger(__name__)

breaker_board = initialize_breaker_board()


class AppReenableSyncWebhooks(BaseMutation):
    app = graphene.Field(
        App,
        description="App for which sync webhooks were re-enabled.",
    )

    class Arguments:
        app_id = graphene.ID(
            description="The app ID to re-enable sync webhooks for.", required=True
        )

    class Meta:
        description = (
            "Re-enable sync webhooks for provided app. "
            "Can be used to manually re-enable sync webhooks for the app before "
            "the cooldown period ends." + ADDED_IN_321
        )
        doc_category = DOC_CATEGORY_APPS
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        app = cls.get_node_or_error(
            info, data.get("app_id"), only_type="App", field="appId"
        )
        if breaker_board:
            app = cast(app_models.App, app)
            error = breaker_board.storage.clear_state_for_app(app.id)
            if error:
                raise ValidationError(
                    {
                        "app_id": ValidationError(
                            f"Cannot re-enable sync webhooks for the app {app.name}.",
                            code=AppErrorCode.INVALID.value,
                        )
                    }
                )
            breaker_board.storage.set_app_state(
                app.id, CircuitBreakerState.CLOSED, int(time.time())
            )
            requestor = get_user_or_app_from_context(info.context)
            logger.info(
                "[App ID: %r] Circuit breaker manually reset by %r.",
                app.id,
                requestor,
            )
        return AppReenableSyncWebhooks(app=app)
