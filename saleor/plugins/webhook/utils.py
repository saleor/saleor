import decimal
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List, Optional

from ...payment.interface import GatewayResponse, PaymentGateway, PaymentMethodInfo

if TYPE_CHECKING:
    from ...app.models import App
    from ...payment.interface import PaymentData


APP_GATEWAY_ID_PREFIX = "app"


@dataclass
class PaymentAppData:
    app_pk: int
    name: str


def to_payment_app_id(app: "App", gateway_id: str) -> "str":
    return f"{APP_GATEWAY_ID_PREFIX}:{app.pk}:{gateway_id}"


def from_payment_app_id(app_gateway_id: str) -> Optional["PaymentAppData"]:
    splitted_id = app_gateway_id.split(":")
    if (
        len(splitted_id) == 3
        and splitted_id[0] == APP_GATEWAY_ID_PREFIX
        and all(splitted_id)
    ):
        try:
            app_pk = int(splitted_id[1])
        except (TypeError, ValueError):
            return None
        else:
            return PaymentAppData(app_pk, name=splitted_id[2])
    return None


def parse_list_payment_gateways_response(
    response_data: Any, app: "App"
) -> List["PaymentGateway"]:
    gateways = []
    for gateway_data in response_data:
        gateway_id = gateway_data.get("id")
        gateway_name = gateway_data.get("name")
        gateway_currencies = gateway_data.get("currencies")
        gateway_config = gateway_data.get("config")

        if gateway_id:
            gateways.append(
                PaymentGateway(
                    id=to_payment_app_id(app, gateway_id),
                    name=gateway_name,
                    currencies=gateway_currencies,
                    config=gateway_config,
                )
            )
    return gateways


def parse_payment_action_response(
    payment_information: "PaymentData",
    response_data: Any,
    transaction_kind: "str",
) -> "GatewayResponse":
    error = response_data.get("error")
    is_success = not error

    payment_method_info = None
    payment_method_data = response_data.get("payment_method")
    if payment_method_data:
        payment_method_info = PaymentMethodInfo(
            brand=payment_method_data.get("brand"),
            exp_month=payment_method_data.get("exp_month"),
            exp_year=payment_method_data.get("exp_year"),
            last_4=payment_method_data.get("last_4"),
            name=payment_method_data.get("name"),
            type=payment_method_data.get("type"),
        )

    amount = payment_information.amount
    if "amount" in response_data:
        try:
            amount = decimal.Decimal(response_data["amount"])
        except decimal.DecimalException:
            pass

    return GatewayResponse(
        action_required=response_data.get("action_required", False),
        action_required_data=response_data.get("action_required_data"),
        amount=amount,
        currency=payment_information.currency,
        customer_id=response_data.get("customer_id"),
        error=error,
        is_success=is_success,
        kind=response_data.get("kind", transaction_kind),
        payment_method_info=payment_method_info,
        raw_response=response_data,
        psp_reference=response_data.get("psp_reference"),
        transaction_id=response_data.get("transaction_id", ""),
        transaction_already_processed=response_data.get(
            "transaction_already_processed", False
        ),
    )
