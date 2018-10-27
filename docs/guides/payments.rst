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

    After completing those steps your new payment gateway will only be
    available from the API level. You will also need to integrate it into your
    Frontend's workflow.

get_client_token(**connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

authorize(payment, payment_token, **connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
            kind=Transactions.AUTH,
            amount=payment.total,
            currency=payment.currency,
            gateway_response=get_payment_gateway_response(response),
            token=response.transaction.id,
            is_success=response.is_success)
        return txn, response['error']


refund(payment, amount, **connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
            kind=Transactions.CAPTURE).first()
        transaction_token = capture_txn.token

        # Handle connecting to the gateway and sending the refund request here
        response = gateway.refund(token=transaction_token)

        txn = create_transaction(
            payment=payment,
            kind=Transactions.REFUND,
            amount=amount,
            currency=payment.currency,
            token=response.transaction.id,
            is_success=response.is_success,
            gateway_response=get_payment_gateway_response(response))
        return txn, response['error']

capture(payment, amount, **connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
            kind=Transactions.AUTH).first()
        transaction_token = auth_transaction.token

        # Handle connecting to the gateway and sending the capture request here
        response = gateway.capture(token=transaction_token)

        txn = create_transaction(
            payment=payment,
            kind=Transactions.CAPTURE,
            amount=amount,
            currency=payment.currency,
            token=response.transaction.id,
            is_success=response.is_success,
            gateway_response=get_payment_gateway_response(response))
        return txn, response['error']

void(payment, **connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A cancellation of a pending authorization or capture.

Example
"""""""

.. code-block:: python

    def void(
            payment: Payment,
            **connection_params: Dict) -> Tuple[Transaction, str]:

        # Please note that token from the last AUTH transaction should be used
        auth_transaction = payment.transactions.filter(
            kind=Transactions.AUTH).first()
        transaction_token = auth_transaction.token

        # Handle connecting to the gateway and sending the void request here
        response = gateway.void(token=transaction_token)

        txn = create_transaction(
            payment=payment,
            kind=Transactions.VOID,
            amount=payment.total,
            currency=payment.currency,
            gateway_response=get_payment_gateway_response(response),
            token=response.transaction.id,
            is_success=response.is_success)
        return txn, response['error']

Parameters
^^^^^^^^^^
+-----------------------+-----------+------------------------------------------------------------------------------------------------+
| name                  | type      | description                                                                                    |
+-----------------------+-----------+------------------------------------------------------------------------------------------------+
| ``payment``           | `Payment` | Payment instance, for which the transaction will be created.                                   |
+-----------------------+-----------+------------------------------------------------------------------------------------------------+
| ``transaction_token`` | `str`     | Unique transaction's token that will be used on the purpose of completing the payment process. |
+-----------------------+-----------+------------------------------------------------------------------------------------------------+
| ``connection_params`` | `dict`    | List of parameters used for connecting to the payment's gateway.                               |
+-----------------------+-----------+------------------------------------------------------------------------------------------------+
| ``amount``            | `Decimal` | Amount of Money to be refunded/captured.                                                       |
+-----------------------+-----------+------------------------------------------------------------------------------------------------+

Returns
^^^^^^^
+-----------------------+---------------+-----------------------------------------------------------------------------------------------------------+
| name                  | type          | description                                                                                               |
+-----------------------+---------------+-----------------------------------------------------------------------------------------------------------+
| ``txn``               | `Transaction` | Transaction created during the payment process, with ``is_success`` set to ``True`` if no error occurred. |
+-----------------------+---------------+-----------------------------------------------------------------------------------------------------------+
| ``error``             | `str`         | Error message to be displayed in the UI, empty if no error occurred.                                      |
+-----------------------+---------------+-----------------------------------------------------------------------------------------------------------+
| ``transaction_token`` | `str`         | Unique transaction's token that will be used on the purpose of completing the payment process.            |
+-----------------------+---------------+-----------------------------------------------------------------------------------------------------------+

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

Handling errors
---------------

Gateway-specific errors should be parsed to Saleor's universal format.
More on this can be found at

Tips
----

- Whenever possible, use ``currency`` and ``amount`` as **returned** by the
  payment gateway, not the one that was sent to it. It might happen, that
  gateway (eg. Braintree) is set to different currency than your shop is.
  In such case, you might want to charge the customer 70 dollars, but due
  to gateway misconfiguration, he will be charged 70 euros.
  Such a situation should be handled, and adequate error should be thrown.

