from typing import Optional

import graphene
from django.core.exceptions import ValidationError

from .....app.models import App
from .....channel.models import Channel
from .....core.exceptions import PermissionDenied
from .....payment.interface import PaymentGatewayData
from .....payment.utils import handle_transaction_initialize_session
from .....permission.enums import PaymentPermissions
from ....app.dataloaders import get_app_promise
from ....channel.enums import TransactionFlowStrategyEnum
from ....core.descriptions import ADDED_IN_313, ADDED_IN_316, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.enums import TransactionInitializeErrorCode
from ....core.scalars import JSON, PositiveDecimal
from ....core.types import common as common_types
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import TransactionEvent, TransactionItem
from ..base import TransactionSessionBase
from .payment_gateway_initialize import PaymentGatewayToInitialize
from .utils import clean_customer_ip_address


class TransactionInitialize(TransactionSessionBase):
    transaction = graphene.Field(
        TransactionItem, description="The initialized transaction."
    )
    transaction_event = graphene.Field(
        TransactionEvent,
        description="The event created for the initialized transaction.",
    )
    data = graphene.Field(
        JSON, description="The JSON data required to finalize the payment."
    )

    class Arguments:
        id = graphene.ID(
            description="The ID of the checkout or order.",
            required=True,
        )
        amount = graphene.Argument(
            PositiveDecimal,
            description=(
                "The amount requested for initializing the payment gateway. "
                "If not provided, the difference between checkout.total - "
                "transactions that are already processed will be send."
            ),
        )
        action = graphene.Argument(
            TransactionFlowStrategyEnum,
            description=(
                "The expected action called for the transaction. By default, the "
                "`channel.defaultTransactionFlowStrategy` will be used. The field "
                "can be used only by app that has `HANDLE_PAYMENTS` permission."
            ),
        )
        customer_ip_address = graphene.String(
            description=(
                "The customer's IP address. If not provided Saleor will try to "
                "determine the customer's IP address on its own. "
                "The customer's IP address will be passed to the payment app. "
                "The IP should be in ipv4 or ipv6 format. "
                "The field can be used only by an app that has `HANDLE_PAYMENTS` "
                "permission." + ADDED_IN_316
            )
        )
        payment_gateway = graphene.Argument(
            PaymentGatewayToInitialize,
            description="Payment gateway used to initialize the transaction.",
            required=True,
        )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS
        description = (
            "Initializes a transaction session. It triggers the webhook "
            "`TRANSACTION_INITIALIZE_SESSION`, to the requested `paymentGateways`. "
            + ADDED_IN_313
            + PREVIEW_FEATURE
        )
        error_type_class = common_types.TransactionInitializeError

    @classmethod
    def clean_action(cls, info, action: Optional[str], channel: "Channel"):
        if not action:
            return channel.default_transaction_flow_strategy
        app = get_app_promise(info.context).get()
        if not app or not app.has_perm(PaymentPermissions.HANDLE_PAYMENTS):
            raise PermissionDenied(permissions=[PaymentPermissions.HANDLE_PAYMENTS])
        return action

    @classmethod
    def clean_app_from_payment_gateway(cls, payment_gateway: PaymentGatewayData) -> App:
        app = App.objects.filter(identifier=payment_gateway.app_identifier).first()
        if not app:
            raise ValidationError(
                {
                    "payment_gateway": ValidationError(
                        message="App with provided identifier not found.",
                        code=TransactionInitializeErrorCode.NOT_FOUND.value,
                    )
                }
            )
        return app

    @classmethod
    def perform_mutation(
        cls,
        root,
        info,
        *,
        id,
        payment_gateway,
        amount=None,
        action=None,
        customer_ip_address=None
    ):
        manager = get_plugin_manager_promise(info.context).get()
        payment_gateway_data = PaymentGatewayData(
            app_identifier=payment_gateway["id"], data=payment_gateway.get("data")
        )
        source_object = cls.clean_source_object(
            info,
            id,
            TransactionInitializeErrorCode.INVALID.value,
            TransactionInitializeErrorCode.NOT_FOUND.value,
            manager=manager,
        )
        action = cls.clean_action(info, action, source_object.channel)
        customer_ip_address = clean_customer_ip_address(
            info,
            customer_ip_address,
            error_code=TransactionInitializeErrorCode.INVALID.value,
        )

        amount = cls.get_amount(
            source_object,
            amount,
        )
        app = cls.clean_app_from_payment_gateway(payment_gateway_data)
        transaction, event, data = handle_transaction_initialize_session(
            source_object=source_object,
            payment_gateway_data=payment_gateway_data,
            amount=amount,
            action=action,
            customer_ip_address=customer_ip_address,
            app=app,
            manager=manager,
        )
        return cls(transaction=transaction, transaction_event=event, data=data)
