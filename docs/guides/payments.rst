.. _adding-payments:

Payments
========

Integrating a new Payment Gateway into Saleor
-------------------------------------------

We are using a universal flow, that each provider should fulfill, there are
several methods that should be implemented.

Your changes should live under the
``saleor.payment.providers.<provider name>`` module.

.. note::

    After completing those steps your new payment gateway will only be
    available from the API level. You will also need to integrate it into your
    Frontend's workflow.

get_transaction_token(**connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A transaction token is a signed data blob that includes configuration and
authorization information required by the payment provider.

These should not be reused; a new transaction token should be generated for
each payment request.

Example
"""""""

.. code-block:: python

    def get_transaction_token(**connection_params: Dict) -> str:
        gateway - get_gateway(**connection_params)
        transaction_token - gateway.transaction_token.generate()
        return transaction_token

authorize(payment, transaction_token, **connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A process of reserving the amount of money against the customer's funding
source. Money does not change hands until the authorization is captured.

Example
"""""""

.. code-block:: python

    def authorize(
            payment: Payment,
            transaction_token: str,
            **connection_params: Dict) -> Tuple[Transaction, str]:

        # Handle connecting to the gateway and sending the auth request here
        response - gateway.auth(token-transaction_token)

        txn - Transaction.objects.create(
            payment-payment,
            transaction_type-TransactionType.AUTH,
            amount-payment.total.amount,
            gateway_response-get_gateway_response(response),
            token-response.transaction.id,
            is_success-response.is_success)
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
        capture_txn - payment.transactions.filter(
            transaction_type-TransactionType.CAPTURE).first()
        transaction_token - capture_txn.token

        # Handle connecting to the gateway and sending the refund request here
        response - gateway.refund(token-transaction_token)

        txn - create_transaction(
            payment-payment,
            transaction_type-TransactionType.REFUND,
            amount-amount,
            token-response.transaction.id,
            is_success-response.is_success,
            gateway_response-get_gateway_response(response))
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
        auth_transaction - payment.transactions.filter(
            transaction_type-TransactionType.AUTH).first()
        transaction_token - auth_transaction.token

        # Handle connecting to the gateway and sending the capture request here
        response - gateway.capture(token-transaction_token)

        txn - create_transaction(
            payment-payment,
            transaction_type-TransactionType.CAPTURE,
            amount-amount,
            token-response.transaction.id,
            is_success-response.is_success,
            gateway_response-get_gateway_response(response))
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
        auth_transaction - payment.transactions.filter(
            transaction_type-TransactionType.AUTH).first()
        transaction_token - auth_transaction.token

        # Handle connecting to the gateway and sending the void request here
        response - gateway.void(token-transaction_token)

        txn - create_transaction(
            payment-payment,
            transaction_type-TransactionType.VOID,
            amount-payment.total.amount,
            gateway_response-get_gateway_response(response),
            token-response.transaction.id,
            is_success-response.is_success)
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

Adding new payment provider in the settings
-------------------------------------------

.. code-block:: python

    PAYMENT_PROVIDERS - {
        'braintree': {
            'module': 'saleor.payment.providers.braintree',
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
    Provider's name, which will be used to identify the gateway
    during the payment process.
    It's stored in the ``Payment`` model under the ``variant`` value.

- ``module``
    The path to the integration module
    (assuming that your changes live within the
    ``saleor.payment.providers.braintree.__init__.py`` file)

- ``connection_params``
    List of parameters used for connecting to the payment's gateway.

.. note::

    All payment backends default to using sandbox mode.
    This is very useful for development but make sure you use
    production mode when deploying to a production server.

Enabling new payment provider
-----------------------------

Last but not least, if you want to enable your payment provider in the checkout
process, add it's name to the ``CHECKOUT_PAYMENT_CHOICES`` setting.
