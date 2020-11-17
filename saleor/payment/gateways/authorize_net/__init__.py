from lxml import etree
from authorizenet import apicontractsv1
from authorizenet.apicontrollers import constants, createTransactionController

from ... import TransactionKind
from ...interface import GatewayConfig, PaymentData, GatewayResponse


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """
    Based on
    https://github.com/AuthorizeNet/sample-code-python/blob/master/AcceptSuite/create-an-accept-payment-transaction.py
    """
    merchant_auth = apicontractsv1.merchantAuthenticationType()
    merchant_auth.name = config.connection_params.get("api_login_id")
    merchant_auth.transactionKey = config.connection_params.get("transaction_key")

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
    transaction_request.transactionType = "authCaptureTransaction"
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

    create_transaction_controller = createTransactionController(
        create_transaction_request
    )
    create_transaction_controller.execute()

    response = create_transaction_controller.getresponse()

    success = False
    error = None
    transaction_id = None
    raw_response = None
    if response is not None:
        raw_response = etree.tostring(response).decode()
        if hasattr(response, "transactionResponse") and hasattr(
            response.transactionResponse, "transId"
        ):
            transaction_id = response.transactionResponse.transId
        if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, "messages"):
                success = True
            else:
                if hasattr(response.transactionResponse, "errors"):
                    error = response.transactionResponse.errors.error[0].errorText
        else:
            if hasattr(response, "transactionResponse") and hasattr(
                response.transactionResponse, "errors"
            ):
                error = response.transactionResponse.errors.error[0].errorText
            else:
                error = response.messages.message[0]["text"].text
    else:
        error = "Null Response"

    if not transaction_id:
        transaction_id = payment_information.token
    return GatewayResponse(
        is_success=success,
        action_required=False,
        transaction_id=transaction_id,
        amount=payment_information.amount,
        currency=payment_information.currency,
        error=error,
        kind=TransactionKind.CAPTURE,
        raw_response=raw_response,
        customer_id=payment_information.customer_id,
    )
