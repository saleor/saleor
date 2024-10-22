import graphene
from django.conf import settings
from django.core.exceptions import ValidationError

from ....core.error_codes import ShopErrorCode
from ....graphql.app.types import App
from ....permission.enums import SitePermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_SHOP
from ...core.mutations import BaseMutation
from ...core.types import ShopError

breaker_board = None
if settings.ENABLE_BREAKER_BOARD:
    from ....webhook.transport.synchronous.circuit_breaker.breaker_board import (
        initialize_breaker_board,
    )

    breaker_board = initialize_breaker_board()


class ReenableSyncWebhooks(BaseMutation):
    app = graphene.Field(
        App,
        description=(
            "Re-enable sync webhooks for the app if circuit breaker was tripped. "
            "Can be used to manually re-enable sync webhooks for the app before "
            "the cooldown period ends."
        ),
    )

    class Arguments:
        app_id = graphene.ID(
            description="The app ID to re-enable sync webhooks for.", required=True
        )

    class Meta:
        description = "Re-enable sync webhooks for provided app."
        doc_category = DOC_CATEGORY_SHOP
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        app = cls.get_node_or_error(info, data.get("app_id"), only_type="App")
        if breaker_board:
            error = breaker_board.storage.clear_state_for_app(app.id)  # type: ignore[union-attr]
            if error:
                raise ValidationError(
                    {
                        "app_id": ValidationError(
                            f"Cannot re-enable sync webhooks for the app {app.name}.",  # type: ignore[union-attr]
                            code=ShopErrorCode.INVALID.value,
                        )
                    }
                )
        return ReenableSyncWebhooks(app=app)
