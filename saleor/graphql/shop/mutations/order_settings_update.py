import graphene
from django.core.exceptions import ValidationError

from ....channel import models as channel_models
from ....permission.enums import OrderPermissions
from ....site.error_codes import OrderSettingsErrorCode
from ...channel.types import OrderSettings
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType, OrderSettingsError


class OrderSettingsUpdateInput(BaseInputObjectType):
    automatically_confirm_all_new_orders = graphene.Boolean(
        required=False,
        description="When disabled, all new orders from checkout "
        "will be marked as unconfirmed. When enabled orders from checkout will "
        "become unfulfilled immediately. By default set to True",
    )
    automatically_fulfill_non_shippable_gift_card = graphene.Boolean(
        required=False,
        description="When enabled, all non-shippable gift card orders "
        "will be fulfilled automatically. By default set to True.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderSettingsUpdate(BaseMutation):
    order_settings = graphene.Field(OrderSettings, description="Order settings.")

    class Arguments:
        input = OrderSettingsUpdateInput(
            required=True, description="Fields required to update shop order settings."
        )

    class Meta:
        description = (
            "Update shop order settings across all channels. "
            "Returns `orderSettings` for the first `channel` in alphabetical order. "
        )
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderSettingsError
        error_type_field = "order_settings_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        FIELDS = [
            "automatically_confirm_all_new_orders",
            "automatically_fulfill_non_shippable_gift_card",
        ]

        channel = (
            channel_models.Channel.objects.filter(is_active=True)
            .order_by("slug")
            .first()
        )

        if channel is None:
            raise ValidationError(
                "There is no active channel available",
                code=OrderSettingsErrorCode.INVALID.value,
            )

        cls.check_channel_permissions(info, [channel.id])

        update_fields = {}
        for field in FIELDS:
            if field in data["input"]:
                update_fields[field] = data["input"][field]

        if update_fields:
            channel_models.Channel.objects.update(**update_fields)

        channel.refresh_from_db()

        order_settings = OrderSettings(
            automatically_confirm_all_new_orders=(
                channel.automatically_confirm_all_new_orders
            ),
            automatically_fulfill_non_shippable_gift_card=(
                channel.automatically_fulfill_non_shippable_gift_card
            ),
            mark_as_paid_strategy=channel.order_mark_as_paid_strategy,
        )
        return OrderSettingsUpdate(order_settings=order_settings)
