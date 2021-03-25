import re
from typing import TYPE_CHECKING, List, Optional

from ...payment.interface import GatewayResponse, PaymentGateway, PaymentMethodInfo

if TYPE_CHECKING:
    from requests.models import Response as RequestsResponse

    from ...app.models import App
    from ...payment.interface import PaymentData


def to_payment_app_id(app: "App", gateway_id: str) -> "str":
    return f"app:{app.pk}:{gateway_id}"


def from_payment_app_id(app_gateway_id: str) -> Optional["int"]:
    pattern = r"^app:(?P<app_pk>[0-9]+):[-a-zA-Z0-9_]+"
    match = re.match(pattern, app_gateway_id)
    app_pk = None
    if match:
        app_pk = match.groupdict().get("app_pk")
    return int(app_pk) if app_pk else None


def webhook_response_to_payment_gateways(
    response: "RequestsResponse", app: "App"
) -> List["PaymentGateway"]:
    response_json = response.json()
    gateways = []
    for gateway_data in response_json:
        gateway_id = gateway_data.get("id")
        gateway_name = gateway_data.get("name")
        gateway_currencies = gateway_data.get("currencies")
        gateway_config = gateway_data.get("config")

        gateways.append(
            PaymentGateway(
                id=to_payment_app_id(app, gateway_id),
                name=gateway_name,
                currencies=gateway_currencies,
                config=gateway_config,
            )
        )
    return gateways


def webhook_response_to_gateway_response(
    payment_information: "PaymentData",
    response: "RequestsResponse",
    transaction_kind: "str",
) -> "GatewayResponse":
    response_json = response.json()

    error = response_json.get("error")
    is_success = response.status_code == 200 and not error

    payment_method_info = PaymentMethodInfo(
        brand=response_json.get("payment_method_brand"),
        exp_month=response_json.get("payment_method_exp_month"),
        exp_year=response_json.get("payment_method_exp_year"),
        last_4=response_json.get("payment_method_last_4"),
        name=response_json.get("payment_method_name"),
        type=response_json.get("payment_method_type"),
    )

    return GatewayResponse(
        action_required=response_json.get("action_required", False),
        action_required_data=response_json.get("action_required_data"),
        amount=payment_information.amount,
        currency=payment_information.currency,
        customer_id=response_json.get("customer_id"),
        error=error,
        is_success=is_success,
        kind=transaction_kind,
        transaction_id=response_json.get("transaction_id"),
        payment_method_info=payment_method_info,
        raw_response=response_json,
    )
