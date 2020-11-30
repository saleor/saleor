import json
from typing import Tuple, Dict, Any, Union
from lxml import etree
import requests
from authorizenet import apicontractsv1
from authorizenet.apicontrollers import constants, createTransactionController

from ... import TransactionKind
from ...interface import GatewayConfig, PaymentData, GatewayResponse, PaymentMethodInfo


def authenticate_test(
    name: str, transaction_key: str, use_sandbox: bool
) -> Tuple[bool, str]:
    """
    Check if credentials are correct.
    This API is not present in the authorizenet Python package.
    https://developer.authorize.net/api/reference/index.html#gettingstarted-section-section-header
    """
    if use_sandbox is True:
        url = constants.SANDBOX
    else:
        url = constants.PRODUCTION
    data = {
        "authenticateTestRequest": {
            "merchantAuthentication": {"name": name, "transactionKey": transaction_key}
        }
    }
    response = requests.post(
        url, json=data, headers={"content-type": "application/json"}
    )
    # Response content is utf-8-sig, which requires usage of json.loads
    result = json.loads(response.content)
    message = ""
    if result.get("messages", {}).get("resultCode") == "Ok":
        return True, ""
    response_message = result.get("messages", {}).get("message")
    if len(response_message) > 0:
        message = response_message[0].get("text", "")
    return False, message


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    return authorize(payment_information, config)


def capture(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    merchant_auth = _get_merchant_auth(config.connection_params)

    transaction_request = apicontractsv1.transactionRequestType()
    transaction_request.transactionType = "priorAuthCaptureTransaction"
    transaction_request.amount = payment_information.amount
    transaction_request.refTransId = payment_information.token

    create_transaction_request = apicontractsv1.createTransactionRequest()
    create_transaction_request.merchantAuthentication = merchant_auth
    create_transaction_request.transactionRequest = transaction_request

    response = _make_request(create_transaction_request, config.connection_params)

    (
        success,
        error,
        transaction_id,
        transaction_response,
        raw_response,
    ) = _handle_authorize_net_response(response)
    payment_method_info = _authorize_net_account_to_payment_method_info(
        transaction_response
    )
    return GatewayResponse(
        is_success=success,
        action_required=False,
        transaction_id=transaction_id,
        amount=payment_information.amount,
        currency=payment_information.currency,
        error=error,
        payment_method_info=payment_method_info,
        kind=TransactionKind.CAPTURE,
        raw_response=raw_response,
        customer_id=payment_information.customer_id,
    )


def authorize(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """
    Based on
    https://github.com/AuthorizeNet/sample-code-python/blob/master/AcceptSuite/create-an-accept-payment-transaction.py
    """
    kind = TransactionKind.CAPTURE if config.auto_capture else TransactionKind.AUTH
    merchant_auth = _get_merchant_auth(config.connection_params)

    # The Saleor token is the authorize.net "opaque data"
    opaque_data = apicontractsv1.opaqueDataType()
    opaque_data.dataDescriptor = "COMMON.ACCEPT.INAPP.PAYMENT"
    opaque_data.dataValue = payment_information.token

    payment_one = apicontractsv1.paymentType()
    payment_one.opaqueData = opaque_data

    order = apicontractsv1.orderType()
    order.invoiceNumber = payment_information.order_id
    order.description = ""

    customer_data = apicontractsv1.customerDataType()
    customer_data.type = "individual"
    customer_data.id = payment_information.customer_id
    customer_data.email = payment_information.customer_email

    transaction_request = apicontractsv1.transactionRequestType()
    transaction_request.transactionType = (
        "authCaptureTransaction" if config.auto_capture else "authOnlyTransaction"
    )
    transaction_request.amount = payment_information.amount
    transaction_request.order = order
    transaction_request.payment = payment_one
    transaction_request.customer = customer_data

    if payment_information.billing:
        customer_address = apicontractsv1.customerAddressType()
        customer_address.firstName = payment_information.billing.first_name
        customer_address.lastName = payment_information.billing.last_name
        customer_address.company = payment_information.billing.company_name
        # authorize.net support says we should not attempt submitting street_address_2
        customer_address.address = payment_information.billing.street_address_1
        customer_address.city = payment_information.billing.city
        customer_address.state = payment_information.billing.country_area
        customer_address.zip = payment_information.billing.postal_code
        customer_address.country = payment_information.billing.country
        transaction_request.billTo = customer_address

    create_transaction_request = apicontractsv1.createTransactionRequest()
    create_transaction_request.merchantAuthentication = merchant_auth
    create_transaction_request.refId = str(payment_information.payment_id)
    create_transaction_request.transactionRequest = transaction_request

    response = _make_request(create_transaction_request, config.connection_params)

    (
        success,
        error,
        transaction_id,
        transaction_response,
        raw_response,
    ) = _handle_authorize_net_response(response)
    searchable_key = None
    if transaction_id:
        searchable_key = transaction_id

    payment_method_info = _authorize_net_account_to_payment_method_info(
        transaction_response
    )

    if not transaction_id:
        transaction_id = payment_information.token

    return GatewayResponse(
        is_success=success,
        action_required=False,
        transaction_id=transaction_id,
        amount=payment_information.amount,
        currency=payment_information.currency,
        error=error,
        payment_method_info=payment_method_info,
        kind=kind,
        raw_response=raw_response,
        customer_id=payment_information.customer_id,
        searchable_key=searchable_key,
    )


def refund(
    payment_information: PaymentData, cc_last_digits: str, config: GatewayConfig
) -> GatewayResponse:
    merchant_auth = _get_merchant_auth(config.connection_params)

    credit_card = apicontractsv1.creditCardType()
    credit_card.cardNumber = cc_last_digits
    credit_card.expirationDate = "XXXX"

    payment = apicontractsv1.paymentType()
    payment.creditCard = credit_card

    transaction_request = apicontractsv1.transactionRequestType()
    transaction_request.transactionType = "refundTransaction"
    transaction_request.amount = payment_information.amount
    # set refTransId to transId of a settled transaction
    transaction_request.refTransId = payment_information.token
    transaction_request.payment = payment

    create_transaction_request = apicontractsv1.createTransactionRequest()
    create_transaction_request.merchantAuthentication = merchant_auth

    create_transaction_request.transactionRequest = transaction_request
    response = _make_request(create_transaction_request, config.connection_params)

    (
        success,
        error,
        transaction_id,
        transaction_response,
        raw_response,
    ) = _handle_authorize_net_response(response)
    payment_method_info = _authorize_net_account_to_payment_method_info(
        transaction_response
    )

    return GatewayResponse(
        is_success=success,
        action_required=False,
        transaction_id=transaction_id,
        amount=payment_information.amount,
        currency=payment_information.currency,
        error=error,
        payment_method_info=payment_method_info,
        kind=TransactionKind.REFUND,
        raw_response=raw_response,
        customer_id=payment_information.customer_id,
    )


def _handle_authorize_net_response(
    response: "ObjectifiedElement",
) -> Tuple[bool, Union[str, None], Union[int, None], str, Any]:
    success = False
    error = None
    transaction_id = None
    transaction_response = None
    raw_response = ""
    if response is not None:
        raw_response = etree.tostring(response).decode()
        if hasattr(response, "transactionResponse"):
            transaction_response = response.transactionResponse[0]
            if hasattr(transaction_response, "transId"):
                transaction_id = transaction_response.transId.pyval
        if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, "messages"):
                success = True
            else:
                if hasattr(response.transactionResponse, "errors"):
                    error = response.transactionResponse.errors.error[0].errorText.pyval
        else:
            if hasattr(response, "transactionResponse") and hasattr(
                response.transactionResponse, "errors"
            ):
                error = response.transactionResponse.errors.error[0].errorText.pyval
            else:
                error = response.messages.message[0]["text"].text
    else:
        error = "Null Response"
    return (
        success,
        error,
        transaction_id,
        transaction_response,
        raw_response,
    )


def _authorize_net_account_to_payment_method_info(
    transaction_response: Union["ObjectifiedElement", None],
) -> PaymentMethodInfo:
    """
    Transform Authorize.Net transactionResponse to Saleor credit card

    accountNumber: "XXXX0015"
    accountType: "Mastercard"

    becomes

    last_4="0015"
    brand="mastercard"
    """
    if (
        transaction_response is not None
        and hasattr(transaction_response, "accountNumber")
        and hasattr(transaction_response, "accountType")
    ):
        return PaymentMethodInfo(
            last_4=transaction_response.accountNumber.pyval.strip("X"),
            brand=transaction_response.accountType.pyval.lower(),
            type="card",
        )


def _get_merchant_auth(connection_params: Dict[str, Any]):
    merchant_auth = apicontractsv1.merchantAuthenticationType()
    merchant_auth.name = connection_params.get("api_login_id")
    merchant_auth.transactionKey = connection_params.get("transaction_key")
    return merchant_auth


def _make_request(create_transaction_request, connection_params: Dict[str, Any]):
    """
    Create an auth.net transaction controller and execute the request
    Returns auth.net response object
    """
    create_transaction_controller = createTransactionController(
        create_transaction_request
    )
    if connection_params.get("use_sandbox") is False:
        create_transaction_controller.setenvironment(constants.PRODUCTION)

    create_transaction_controller.execute()

    response = create_transaction_controller.getresponse()
    return response
