from typing import TYPE_CHECKING, List

from ...payment.interface import GatewayResponse, PaymentGateway, PaymentMethodInfo

if TYPE_CHECKING:
    from requests.models import Response as RequestsResponse

    from ...app.models import App
    from ...payment.interface import PaymentData


def to_payment_app_id(app: "App") -> "str":
    return f"app:{app.pk}"


def from_payment_app_id(app_id: str) -> "int":
    return int(app_id.split(":")[1])


def webhook_response_to_payment_gateways(
    response: "RequestsResponse",
) -> List["PaymentGateway"]:
    response_json = response.json()
    gateways = []
    for gateway_data in response_json:
        gateway_id = gateway_data.get("id")
        gateway_name = gateway_data.get("name")
        gateway_currencies = gateway_data.get("currencies")
        gateway_config = gateway_data.get("config")

        # TODO: fix gateway_id to include app pk
        gateways.append(
            PaymentGateway(
                id=gateway_id,
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
