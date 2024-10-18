import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string

from ....core.error_codes import ShopErrorCode
from ....graphql.app.types import App
from ....permission.enums import SitePermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_SHOP
from ...core.mutations import BaseMutation
from ...core.types import ShopError

# TODO: make breaker_board instance a singleton
breaker_board = None
if settings.ENABLE_BREAKER_BOARD:
    from ....webhook.transport.synchronous.circuit_breaker.breaker_board import (
        BreakerBoard,
    )

    breaker_board = BreakerBoard(
        storage=import_string(settings.BREAKER_BOARD_STORAGE_CLASS_STRING)(),  # type: ignore[arg-type]
        failure_threshold=settings.BREAKER_BOARD_FAILURE_THRESHOLD_PERCENTAGE,
        failure_min_count=settings.BREAKER_BOARD_FAILURE_MIN_COUNT,
        cooldown_seconds=settings.BREAKER_BOARD_COOLDOWN_SECONDS,
        ttl_seconds=settings.BREAKER_BOARD_TTL_SECONDS,
    )


class CloseBreaker(BaseMutation):
    app = graphene.Field(App, description="App which circuit breaker was closed.")

    class Arguments:
        app_id = graphene.ID(description="The app ID to close the breaker.")

    class Meta:
        description = "Close circuit breaker for provided app."
        doc_category = DOC_CATEGORY_SHOP
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        if not breaker_board:
            raise ValidationError(
                {
                    "configuration": ValidationError(
                        "Circuit breaker feature is disabled.",
                        code=ShopErrorCode.INVALID.value,
                    )
                }
            )
        app = cls.get_node_or_error(info, data.get("app_id"), only_type="App")
        breaker_board.storage.close_breaker(app.id)  # type: ignore[union-attr]
        return CloseBreaker(app=app)
