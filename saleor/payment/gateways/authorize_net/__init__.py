from lxml import etree
from authorizenet import apicontractsv1
from authorizenet.apicontrollers import constants, createTransactionController

from ... import TransactionKind
from ...interface import GatewayConfig, PaymentData, GatewayResponse


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    merchantAuth = apicontractsv1.merchantAuthenticationType()
    merchantAuth.name = config.connection_params.get("api_login_id")
    merchantAuth.transactionKey = config.connection_params.get("transaction_key")

    # Set the transaction's refId
    refId = str(payment_information.payment_id)

    # Create the payment object for a payment nonce
    opaqueData = apicontractsv1.opaqueDataType()
    opaqueData.dataDescriptor = "COMMON.ACCEPT.INAPP.PAYMENT"
    opaqueData.dataValue = payment_information.token

    # Add the payment data to a paymentType object
    paymentOne = apicontractsv1.paymentType()
    paymentOne.opaqueData = opaqueData

    # Create order information
    order = apicontractsv1.orderType()
    order.invoiceNumber = payment_information.order_id
    order.description = ""

    # Set the customer's Bill To address
    customerAddress = apicontractsv1.customerAddressType()
    customerAddress.firstName = payment_information.billing.first_name
    customerAddress.lastName = payment_information.billing.last_name
    customerAddress.company = payment_information.billing.company_name
    customerAddress.address = payment_information.billing.street_address_1
    customerAddress.city = payment_information.billing.city
    customerAddress.state = payment_information.billing.country_area
    customerAddress.zip = payment_information.billing.postal_code
    customerAddress.country = payment_information.billing.country

    # Set the customer's identifying information
    customerData = apicontractsv1.customerDataType()
    customerData.type = "individual"
    customerData.id = payment_information.customer_id
    customerData.email = payment_information.customer_email

    # Create a transactionRequestType object and add the previous objects to it
    transactionrequest = apicontractsv1.transactionRequestType()
    transactionrequest.transactionType = "authCaptureTransaction"
    transactionrequest.amount = payment_information.amount
    transactionrequest.order = order
    transactionrequest.payment = paymentOne
    transactionrequest.billTo = customerAddress
    transactionrequest.customer = customerData

    # Assemble the complete transaction request
    createtransactionrequest = apicontractsv1.createTransactionRequest()
    createtransactionrequest.merchantAuthentication = merchantAuth
    createtransactionrequest.refId = refId
    createtransactionrequest.transactionRequest = transactionrequest

    # Create the controller and get response
    createtransactioncontroller = createTransactionController(createtransactionrequest)
    createtransactioncontroller.execute()

    response = createtransactioncontroller.getresponse()
    print(response.messages.message[0]["text"])
    print(response.transactionResponse)

    error = None
    raw_response = etree.tostring(response).decode()
    if response is not None:
        if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, "messages") == True:
                message = response.transactionResponse.messages.message[0]
                return GatewayResponse(
                    is_success=True,
                    action_required=False,
                    transaction_id=response.transactionResponse.transId,
                    amount=payment_information.amount,
                    currency=payment_information.currency,
                    error=error,
                    kind=TransactionKind.CAPTURE,
                    raw_response=raw_response,
                    customer_id=payment_information.customer_id,
                )
            else:
                if hasattr(response.transactionResponse, "errors") == True:
                    message = response.transactionResponse.errors.error[0].errorText
        else:
            if (
                hasattr(response, "transactionResponse") == True
                and hasattr(response.transactionResponse, "errors") == True
            ):
                message = response.transactionResponse.errors.error[0].errorText
            else:
                message = response.messages.message[0]["text"].text
    else:
        message = "Null Response"

    return result
