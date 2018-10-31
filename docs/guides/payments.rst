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

get_client_token(\*\*connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A client token is a signed data blob that includes configuration and
authorization information required by the payment gateway.

These should not be reused; a new client token should be generated for
each payment request.

Example
"""""""

.. code-block:: python

    def get_client_token(**connection_params: Dict) -> str:
        gateway = get_payment_gateway(**connection_params)
        client_token = gateway.client_token.generate()
        return client_token

authorize(payment, payment_token, \*\*connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A process of reserving the amount of money against the customer's funding
source. Money does not change hands until the authorization is captured.

Example
"""""""

.. code-block:: python

    def authorize(
            payment: Payment,
            payment_token: str,
            **connection_params: Dict) -> Tuple[Transaction, str]:

        # Handle connecting to the gateway and sending the auth request here
        response = gateway.authorize(token=payment_token)

        txn = Transaction.objects.create(
            payment=payment,
            kind=TransactionKind.AUTH,
            amount=response.amount,
            currency=response.currency,
            gateway_response=get_payment_gateway_response(response),
            token=response.transaction.id,
            error=get_error(response),
            is_success=response.is_success)
        return txn, response['error']

refund(payment, amount, \*\*connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Full or partial return of captured funds to the customer.

Example
"""""""

.. code-block:: python

    def refund(
            payment: Payment,
            amount: Decimal,
            **connection_params: Dict) -> Tuple[Transaction, str]:

        # Please note that token from the last AUTH transaction should be used
        capture_txn = payment.transactions.filter(
            kind=TransactionKind.CAPTURE).first()
        transaction_token = capture_txn.token

        # Handle connecting to the gateway and sending the refund request here
        response = gateway.refund(token=transaction_token)

        txn = create_transaction(
            payment=payment,
            kind=TransactionKind.REFUND,
            amount=response.amount,
            currency=response.currency,
            token=response.transaction.id,
            error=get_error(response),
            is_success=response.is_success,
            gateway_response=get_payment_gateway_response(response))
        return txn, response['error']

capture(payment, amount, \*\*connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A transfer of the money that was reserved during the authorization stage.

Example
"""""""

.. code-block:: python

    def capture(
            payment: Payment,
            amount: Decimal,
            **connection_params: Dict) -> Tuple[Transaction, str]:

        # Please note that token from the last AUTH transaction should be used
        auth_transaction = payment.transactions.filter(
            kind=TransactionKind.AUTH).first()
        transaction_token = auth_transaction.token

        # Handle connecting to the gateway and sending the capture request here
        response = gateway.capture(token=transaction_token)

        txn = create_transaction(
            payment=payment,
            kind=TransactionKind.CAPTURE,
            amount=response,
            currency=response.currency,
            token=response.transaction.id,
            error=get_error(response),
            is_success=response.is_success,
            gateway_response=get_payment_gateway_response(response))
        return txn, response['error']

void(payment, \*\*connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A cancellation of a pending authorization or capture.

Example
"""""""

.. code-block:: python

    def void(
            payment: Payment,
            **connection_params: Dict) -> Tuple[Transaction, str]:

        # Please note that token from the last AUTH transaction should be used
        auth_transaction = payment.transactions.filter(
            kind=TransactionKind.AUTH).first()
        transaction_token = auth_transaction.token

        # Handle connecting to the gateway and sending the void request here
        response = gateway.void(token=transaction_token)

        txn = create_transaction(
            payment=payment,
            kind=TransactionKind.VOID,
            amount=response.amount,
            currency=response.currency,
            error=get_error(response),
            gateway_response=get_payment_gateway_response(response),
            token=response.transaction.id,
            is_success=response.is_success)
        return txn, response['error']

charge(payment, payment_token, amount, \*\*connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Authorization and capture in a single step.

Example
"""""""

.. code-block:: python

    def charge(
            payment: Payment,
            payment_token: str,
            amount: Decimal,
            **connection_params: Dict) -> Tuple[Transaction, str]:

        # Handle connecting to the gateway and sending the charge request here
        response = gateway.charge(token=payment_token, amount=amount)

        txn = create_transaction(
            payment=payment,
            kind=TransactionKind.CHARGE,
            amount=response.amount,
            currency=response.currency,
            error=get_error(response),
            gateway_response=get_payment_gateway_response(response),
            token=response.transaction.id,
            is_success=response.is_success)
        return txn, response['error']

Parameters
^^^^^^^^^^

+-----------------------+-------------+------------------------------------------------------------------------------------+
| name                  | type        | description                                                                        |
+-----------------------+-------------+------------------------------------------------------------------------------------+
| ``payment``           | ``Payment`` | Payment instance, for which the transaction will be created.                       |
+-----------------------+-------------+------------------------------------------------------------------------------------+
| ``client_token``      | ``str``     | Unique client's token that will be used as his indentifier in the payment process. |
+-----------------------+-------------+------------------------------------------------------------------------------------+
| ``connection_params`` | ``dict``    | List of parameters used for connecting to the payment's gateway.                   |
+-----------------------+-------------+------------------------------------------------------------------------------------+
| ``amount``            | ``Decimal`` | Amount of Money to be refunded/captured.                                           |
+-----------------------+-------------+------------------------------------------------------------------------------------+

Returns
^^^^^^^

+------------------+-----------------+-----------------------------------------------------------------------------------------------------------+
| name             | type            | description                                                                                               |
+------------------+-----------------+-----------------------------------------------------------------------------------------------------------+
| ``txn``          | ``Transaction`` | Transaction created during the payment process, with ``is_success`` set to ``True`` if no error occurred. |
+------------------+-----------------+-----------------------------------------------------------------------------------------------------------+
| ``error``        | ``str``         | Error message to be displayed in the UI, empty if no error occurred.                                      |
+------------------+-----------------+-----------------------------------------------------------------------------------------------------------+
| ``client_token`` | ``str``         | Unique client's token that will be used as his indentifier in the payment process.                        |
+------------------+-----------------+-----------------------------------------------------------------------------------------------------------+

Handling errors
---------------

Gateway-specific errors should be parsed to Saleor's universal format.
More on this can be found in :ref:`payments`.

Adding payment method to the old checkout (optional)
----------------------------------------------------

If you are not using SPA Storefront, there are some additional steps you need
to perform in order to enable the payment method in your checkout flow.

Add PaymentForm
^^^^^^^^^^^^^^^

Payment on the storefront will be handled via payment form, it should
implement all the steps necessary for the payment to succeed.
All payment forms should inherit from ``PaymentForm``.

Your changes should live under
``saleor.payment.gateways.<gateway name>.forms.py``

Example
"""""""

.. code-block:: python

    class BraintreePaymentForm(PaymentForm):
        amount = forms.DecimalField()
        payment_method_nonce = forms.CharField()

        def process_payment(self):
            payment_token = self.cleaned_data['payment_method_nonce']
            self.payment.token = payment_token
            self.payment.save(update_fields=['token'])
            amount = self.cleaned_data['amount']
            self.payment.charge(payment_token, amount)

Implement get_form_class()
^^^^^^^^^^^^^^^^^^^^^^^^^^

Should return the form that will be used for the checkout process.

.. note::
    Should be added as a part of the provider's methods.

Example
"""""""

    .. code-block:: python

        def get_form_class():
            return BraintreePaymentForm

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
            'module': 'saleor.payment.gateways.braintree',
            'connection_params': {
                'sandbox_mode': get_bool_from_env('BRAINTREE_SANDBOX_MODE', True),
                'merchant_id': os.environ.get('BRAINTREE_MERCHANT_ID'),
                'public_key': os.environ.get('BRAINTREE_PUBLIC_KEY'),
                'private_key': os.environ.get('BRAINTREE_PRIVATE_KEY')
            }
        }
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

