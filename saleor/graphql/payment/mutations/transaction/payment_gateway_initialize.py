import graphene
from django.conf import settings

from .....payment.interface import PaymentGatewayData
from ....core.descriptions import ADDED_IN_313, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.enums import PaymentGatewayInitializeErrorCode
from ....core.scalars import JSON, PositiveDecimal
from ....core.types import BaseInputObjectType, BaseObjectType
from ....core.types import common as common_types
from ....plugins.dataloaders import get_plugin_manager_promise
from ..base import TransactionSessionBase


class PaymentGatewayConfig(BaseObjectType):
    id = graphene.String(required=True, description="The app identifier.")
    data = graphene.Field(
        JSON, description="The JSON data required to initialize the payment gateway."
    )
    errors = common_types.NonNullList(common_types.PaymentGatewayConfigError)

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentGatewayToInitialize(BaseInputObjectType):
    id = graphene.String(
        required=True,
        description="The identifier of the payment gateway app to initialize.",
    )
    data = graphene.Field(
        JSON, description="The data that will be passed to the payment gateway."
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentGatewayInitialize(TransactionSessionBase):
    gateway_configs = common_types.NonNullList(
        PaymentGatewayConfig, description="List of payment gateway configurations."
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
        payment_gateways = graphene.List(
            graphene.NonNull(PaymentGatewayToInitialize),
            description="List of payment gateways to initialize.",
            required=False,
        )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS
        description = (
            "Initializes a payment gateway session. It triggers the webhook "
            "`PAYMENT_GATEWAY_INITIALIZE_SESSION`, to the requested `paymentGateways`. "
            "If `paymentGateways` is not provided, the webhook will be send to all "
            "subscribed payment gateways. There is a limit of "
            f"{settings.TRANSACTION_ITEMS_LIMIT} transaction items per checkout / order."
            + ADDED_IN_313
            + PREVIEW_FEATURE
        )
        error_type_class = common_types.PaymentGatewayInitializeError

    @classmethod
    def prepare_response(
        cls,
        payment_gateways_input: list[PaymentGatewayData],
        payment_gateways_response: list[PaymentGatewayData],
    ) -> list[PaymentGatewayConfig]:
        response = []
        payment_gateways_response_dict = {
            gateway.app_identifier: gateway for gateway in payment_gateways_response
        }

        payment_gateways_input_dict = (
            {gateway.app_identifier: gateway for gateway in payment_gateways_input}
            if payment_gateways_input
            else payment_gateways_response_dict
        )
        for identifier in payment_gateways_input_dict:
            app_identifier = identifier
            payment_gateway_response = payment_gateways_response_dict.get(identifier)
            if payment_gateway_response:
                response_data = payment_gateway_response.data
                errors = []
                if payment_gateway_response.error:
                    code = common_types.PaymentGatewayConfigErrorCode.INVALID.value
                    errors = [
                        {
                            "field": "id",
                            "message": payment_gateway_response.error,
                            "code": code,
                        }
                    ]

            else:
                response_data = None
                code = common_types.PaymentGatewayConfigErrorCode.NOT_FOUND.value
                msg = (
                    "Active app with `HANDLE_PAYMENT` permissions or "
                    "app webhook not found."
                )
                errors = [
                    {
                        "field": "id",
                        "message": msg,
                        "code": code,
                    }
                ]
            data_to_return = response_data.get("data") if response_data else None
            response.append(
                PaymentGatewayConfig(
                    id=app_identifier, data=data_to_return, errors=errors
                )
            )
        return response

    @classmethod
    def perform_mutation(cls, root, info, *, id, amount=None, payment_gateways=None):
        manager = get_plugin_manager_promise(info.context).get()
        source_object = cls.clean_source_object(
            info,
            id,
            PaymentGatewayInitializeErrorCode.INVALID.value,
            PaymentGatewayInitializeErrorCode.NOT_FOUND.value,
            manager=manager,
        )
        payment_gateways_data = []
        if payment_gateways:
            payment_gateways_data = [
                PaymentGatewayData(
                    app_identifier=gateway["id"], data=gateway.get("data")
                )
                for gateway in payment_gateways
            ]
        amount = cls.get_amount(source_object, amount)
        response_data = manager.payment_gateway_initialize_session(
            amount, payment_gateways_data, source_object
        )
        return cls(
            gateway_configs=cls.prepare_response(payment_gateways_data, response_data),
            errors=[],
        )
