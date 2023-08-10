import graphene
from django.core.exceptions import ValidationError

from .....channel.models import Channel
from .....payment import PaymentError
from .....payment.error_codes import PaymentErrorCode
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.fields import JSONString
from ....core.mutations import BaseMutation
from ....core.types import common as common_types
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import PaymentInitialized


class PaymentInitialize(BaseMutation):
    initialized_payment = graphene.Field(
        PaymentInitialized, required=False, description="Payment that was initialized."
    )

    class Arguments:
        gateway = graphene.String(
            description="A gateway name used to initialize the payment.",
            required=True,
        )
        channel = graphene.String(
            description="Slug of a channel for which the data should be returned.",
        )
        payment_data = JSONString(
            required=False,
            description=(
                "Client-side generated data required to initialize the payment."
            ),
        )

    class Meta:
        description = "Initializes payment process when it is required by gateway."
        doc_category = DOC_CATEGORY_PAYMENTS
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def validate_channel(cls, channel_slug):
        try:
            channel = Channel.objects.get(slug=channel_slug)
        except Channel.DoesNotExist:
            raise ValidationError(
                {
                    "channel": ValidationError(
                        f"Channel with '{channel_slug}' slug does not exist.",
                        code=PaymentErrorCode.NOT_FOUND.value,
                    )
                }
            )
        if not channel.is_active:
            raise ValidationError(
                {
                    "channel": ValidationError(
                        f"Channel with '{channel_slug}' is inactive.",
                        code=PaymentErrorCode.CHANNEL_INACTIVE.value,
                    )
                }
            )
        return channel

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, channel, gateway, payment_data
    ):
        cls.validate_channel(channel_slug=channel)
        manager = get_plugin_manager_promise(info.context).get()
        try:
            response = manager.initialize_payment(
                gateway, payment_data, channel_slug=channel
            )
        except PaymentError as e:
            raise ValidationError(
                {
                    "payment_data": ValidationError(
                        str(e), code=PaymentErrorCode.INVALID.value
                    )
                }
            )
        return PaymentInitialize(initialized_payment=response)
