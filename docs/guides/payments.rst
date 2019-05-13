.. _adding-payments:

Payments
========

Integrating a new Payment Gateway into Saleor
---------------------------------------------

We are using a universal flow, that each gateway should fulfill, there are
several methods that should be implemented.

Your changes should live under the
``saleor.payment.gateways.<gateway name>`` module.

.. note::

    After completing those steps you will also need to integrate your payment
    gateway into your SPA Storefront's workflow.

get_client_token(connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A client token is a signed data blob that includes configuration and
authorization information required by the payment gateway.

These should not be reused; a new client token should be generated for
each payment request.

Example
"""""""

.. code-block:: python

    def get_client_token(connection_params: Dict) -> str:
        gateway = get_payment_gateway(**connection_params)
        client_token = gateway.client_token.generate()
        return client_token


.. note::

    All the below functions receive ``payment_information`` as a dataclass: ``PaymentData`` and ``config`` as a dataclass: ``ConfigData``. 
    Functions should return a response as a dataclass: ``GatewayResponse``. 
    The description of the given structures can be found below.


authorize(payment_information, config)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A process of reserving the amount of money against the customer's funding
source. Money does not change hands until the authorization is captured.

Example
"""""""

.. code-block:: python

    def authorize(
            payment_information: PaymentData,
            config: ConfigData) -> GatewayResponse:

        # Handle connecting to the gateway and sending the auth request here
        response = gateway.authorize(token=payment_information.token)

        # Return a correct response format so Saleor can process it,
        # the response must be json serializable
        return GatewayResponse(
            is_success=response.is_success,
            transaction_id=response.transaction.id,
            kind=TransactionKind.AUTH,
            amount=response.amount,
            currency=response.currency,
            error=get_error(response),
            raw_response=get_payment_gateway_response(response),
        )

refund(payment_information, config)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Full or partial return of captured funds to the customer.

Example
"""""""

.. code-block:: python

    def refund(
            payment_information: PaymentData,
            config: ConfigData) -> GatewayResponse:

        # Handle connecting to the gateway and sending the refund request here
        response = gateway.refund(token=payment_information.token)

        # Return a correct response format so Saleor can process it,
        # the response must be json serializable
        return GatewayResponse(
            is_success=response.is_success,
            transaction_id=response.transaction.id,
            kind=TransactionKind.REFUND,
            amount=response.amount,
            currency=response.currency,
            error=get_error(response),
            raw_response=get_payment_gateway_response(response),
        )

capture(payment_information, config)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A transfer of the money that was reserved during the authorization stage.

Example
"""""""

.. code-block:: python

    def capture(
            payment_information: PaymentData,
            config: ConfigData) -> GatewayResponse:

        # Handle connecting to the gateway and sending the capture request here
        response = gateway.capture(token=payment_information.token)

        # Return a correct response format so Saleor can process it,
        # the response must be json serializable
        return GatewayResponse(
            is_success=response.is_success,
            transaction_id=response.transaction.id,
            kind=TransactionKind.CAPTURE,
            amount=response.amount,
            currency=response.currency,
            error=get_error(response),
            raw_response=get_payment_gateway_response(response),
        )

void(payment_information, config)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A cancellation of a pending authorization or capture.

Example
"""""""

.. code-block:: python

    def void(
            payment_information: PaymentData,
            config: ConfigData) -> GatewayResponse:

        # Handle connecting to the gateway and sending the void request here
        response = gateway.void(token=payment_information.token)

        # Return a correct response format so Saleor can process it,
        # the response must be json serializable
        return GatewayResponse(
            is_success=response.is_success,
            transaction_id=response.transaction.id,
            kind=TransactionKind.VOID,
            amount=response.amount,
            currency=response.currency,
            error=get_error(response),
            raw_response=get_payment_gateway_response(response),
        )

charge(payment_information, config)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Authorization and capture in a single step.

Example
"""""""

.. code-block:: python

    def charge(
            payment_information: PaymentData,
            config: ConfigData) -> GatewayResponse:

        # Handle connecting to the gateway and sending the charge request here
        response = gateway.charge(
            token=payment_information.token,
            amount=payment_information.amount)

        # Return a correct response format so Saleor can process it,
        # the response must be json serializable
        return GatewayResponse(
            is_success=response.is_success,
            transaction_id=response.transaction.id,
            kind=TransactionKind.CHARGE,
            amount=response.amount,
            currency=response.currency,
            error=get_error(response),
            raw_response=get_payment_gateway_response(response),
        )

process_payment(payment_information, config)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Used for the checkout process, it should perform all the necessary
steps to process a payment. It should use already defined functions,
like authorize and capture.

Example
"""""""

.. code-block:: python

    def process_payment(
            payment_information: PaymentData,
            config: ConfigData) -> GatewayResponse:

        # Authorize, update the token, then capture
        authorize_response = authorize(
            payment_information, config)
        payment_information.token = authorize_response.transaction_id

        capture_response = capture(
            payment_information, config)

        return capture_response

Parameters
^^^^^^^^^^

+-------------------------+-----------------+-----------------------------------------------------------------------------+
| name                    | type            | description                                                                 |
+-------------------------+-----------------+-----------------------------------------------------------------------------+
| ``payment_information`` | ``PaymentData`` | Payment information, containing the token, amount, currency and billing.    |
+-------------------------+-----------------+-----------------------------------------------------------------------------+
| ``config``              | ``ConfigData``  | Configuration of the payment gateway.                                               |
+-------------------------+-----------------+-----------------------------------------------------------------------------+

PaymentData
"""""""""""

+---------------------+-----------------+-----------------------------------------------------------------+
| name                | type            | description                                                     |
+---------------------+-----------------+-----------------------------------------------------------------+
| token               | ``str``         | Token used for transaction, provided by the gateway.            |
+---------------------+-----------------+-----------------------------------------------------------------+
| amount              | ``Decimal``     | Amount to be authorized/captured/charged/refunded.              |
+---------------------+-----------------+-----------------------------------------------------------------+
| billing             | ``AddressData`` | Billing information.                                            |
+---------------------+-----------------+-----------------------------------------------------------------+
| shipping            | ``AddressData`` | Shipping information.                                           |
+---------------------+-----------------+-----------------------------------------------------------------+
| order_id            | ``int``         | Order id.                                                       |
+---------------------+-----------------+-----------------------------------------------------------------+
| customer_ip_address | ``str``         | IP address of the customer                                      |
+---------------------+-----------------+-----------------------------------------------------------------+
| customer_email      | ``str``         | Email address of the customer.                                  |
+---------------------+-----------------+-----------------------------------------------------------------+


AddressData
"""""""""""

+------------------+---------+
| name             | type    |
+------------------+---------+
| first_name       | ``str`` |
+------------------+---------+
| last_name        | ``str`` |
+------------------+---------+
| company_name     | ``str`` |
+------------------+---------+
| street_address_1 | ``str`` |
+------------------+---------+
| street_address_2 | ``str`` |
+------------------+---------+
| city             | ``str`` |
+------------------+---------+
| city_area        | ``str`` |
+------------------+---------+
| postal_code      | ``str`` |
+------------------+---------+
| country          | ``str`` |
+------------------+---------+
| country_area     | ``str`` |
+------------------+---------+
| phone            | ``str`` |
+------------------+---------+

ConfigData
""""""""""

+---------------------+-----------+---------------------------------------------------------------------------------------------------------+
| name                | type      | description                                                                                             |
+---------------------+-----------+---------------------------------------------------------------------------------------------------------+
| auto_capture        | ``bool``  | Define if gateway should also capture funds from the card. If false, payment should be only authorized  |
+---------------------+-----------+---------------------------------------------------------------------------------------------------------+
| template_path       | ``str``   | Should specify a path to a template that will be rendered for the checkout.                             |
+---------------------+-----------+---------------------------------------------------------------------------------------------------------+
| connection_params   | ``Dict``  | List of parameters used for connecting to the payment’s gateway.                                        |
+---------------------+-----------+---------------------------------------------------------------------------------------------------------+


Returns
^^^^^^^

+----------------------+----------------------------+------------------------------------------------------------------------------------------------------------------------+
| name                 | type                       | description                                                                                                            |
+----------------------+----------------------------+------------------------------------------------------------------------------------------------------------------------+
| ``gateway_response`` | ``GatewayResponse``        | GatewayResponse containing details about every transaction, with ``is_success`` set to ``True`` if no error occurred.  |
+----------------------+----------------------------+------------------------------------------------------------------------------------------------------------------------+
| ``client_token``     | ``str``                    | Unique client's token that will be used as his indentifier in the payment process.                                     |
+----------------------+----------------------------+------------------------------------------------------------------------------------------------------------------------+


GatewayResponse
"""""""""""""""

+----------------+-------------+--------------------------------------------------------------------------+
| name           | type        | description                                                              |
+----------------+-------------+--------------------------------------------------------------------------+
| transaction_id | ``str``     | Transaction ID as returned by the gateway.                               |
+----------------+-------------+--------------------------------------------------------------------------+
| kind           | ``str``     | Transaction kind, one of: auth, capture, charge, refund, void.           |
+----------------+-------------+--------------------------------------------------------------------------+
| is_success     | ``bool``    | Status whether the transaction was successful or not.                    |
+----------------+-------------+--------------------------------------------------------------------------+
| amount         | ``Decimal`` | Amount that the gateway actually charged or authorized.                  |
+----------------+-------------+--------------------------------------------------------------------------+
| currency       | ``str``     | Currency in which the gateway charged, needs to be an ISO 4217 code.     |
+----------------+-------------+--------------------------------------------------------------------------+
| error          | ``str``     | An error message if one occured. Should be ``None`` if no error occured. |
+----------------+-------------+--------------------------------------------------------------------------+
| raw_response   | ``dict``     | Raw gateway response as a dict object. By default it is ``None``        |
+----------------+-------------+--------------------------------------------------------------------------+


Handling errors
---------------

Gateway-specific errors should be parsed to Saleor's universal format.
More on this can be found in :ref:`payments-architecture`.

Adding payment method to the old checkout (optional)
----------------------------------------------------

If you are not using SPA Storefront, there are some additional steps you need
to perform in order to enable the payment method in your checkout flow.

Add a Form
^^^^^^^^^^

Payment on the storefront will be handled via payment form, it should
implement all the steps necessary for the payment to succeed. The form
must implement `get_payment_token` that returns a token required to process
payments. All payment forms should inherit from ``django.forms.Form``.

Your changes should live under
``saleor.payment.gateways.<gateway name>.forms.py``

Example
"""""""

.. code-block:: python

    class BraintreePaymentForm(forms.Form):
        amount = forms.DecimalField()
        payment_method_nonce = forms.CharField()

        def get_payment_token(self):
            return self.cleaned_data['payment_method_nonce']

Implement create_form(data, payment_information, connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Should return the form that will be used for the checkout process.

.. note::
    Should be added as a part of the provider's methods.

Example
"""""""

    .. code-block:: python

        def create_form(data, payment_information, connection_params):
            return BraintreePaymentForm(
                data, payment_information, connection_params)


Implement template_path
^^^^^^^^^^^^^^^^^^^^^^^

Should specify a path to a template that will be rendered for the checkout.

.. code-block:: python

    PAYMENT_GATEWAYS = {
        DUMMY: {
            "module": "saleor.payment.gateways.dummy",
            "config": {
                "auto_capture": True,
                "connection_params": {},
                "template_path": "order/payment/dummy.html",
            },
        },
    }


Add template
^^^^^^^^^^^^

Add a new template to handle the payment process with your payment form.
Your changes should live under
``saleor.templates.order.payment.<gateway name>.html``

Adding new payment gateway to the settings
------------------------------------------

.. code-block:: python

    PAYMENT_GATEWAYS = {
        'braintree': {
            "module": "saleor.payment.gateways.braintree",
            "config": {
                "auto_capture": True,
                "template_path": "order/payment/braintree.html",
                "connection_params": {
                    "sandbox_mode": get_bool_from_env("BRAINTREE_SANDBOX_MODE", True),
                    "merchant_id": os.environ.get("BRAINTREE_MERCHANT_ID"),
                    "public_key": os.environ.get("BRAINTREE_PUBLIC_KEY"),
                    "private_key": os.environ.get("BRAINTREE_PRIVATE_KEY"),
                },
            },
        },
    }

Please take a moment to consider the example settings above.

- ``braintree``
    Gateway's name, which will be used to identify the gateway
    during the payment process.
    It's stored in the ``Payment`` model under the ``gateway`` value.

- ``module``
    The path to the integration module
    (assuming that your changes live within the
    ``saleor.payment.gateways.braintree.__init__.py`` file)

- ``connection_params``
    List of parameters used for connecting to the payment's gateway.

- ``auto_capture``
    Define if the gateway should also capture funds from the card. When auto_capture is set to False, funds will be blocked but manual capture will be required.

.. note::

    All payment backends default to using sandbox mode.
    This is very useful for development but make sure you use
    production mode when deploying to a production server.

Enabling new payment gateway
----------------------------

Last but not least, if you want to enable your payment gateway in the checkout
process, add it's name to the ``CHECKOUT_PAYMENT_GATEWAYS`` setting.

Tips
----

- Whenever possible, use ``currency`` and ``amount`` as **returned** by the
  payment gateway, not the one that was sent to it. It might happen, that
  gateway (eg. Braintree) is set to different currency than your shop is.
  In such case, you might want to charge the customer 70 dollars, but due
  to gateway misconfiguration, he will be charged 70 euros.
  Such a situation should be handled, and adequate error should be thrown.

