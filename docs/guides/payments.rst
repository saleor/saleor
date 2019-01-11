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

authorize(payment_information, \*\*connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A process of reserving the amount of money against the customer's funding
source. Money does not change hands until the authorization is captured.

Example
"""""""

.. code-block:: python

    def authorize(
            payment_information: Dict,
            **connection_params: Dict) -> Dict:

        # Handle connecting to the gateway and sending the auth request here
        response = gateway.authorize(token=payment_information['token'])

        # Return a correct response format so Saleor can process it,
        # the response must be json serializable
        return {
            'is_success': response.is_success,
            'transaction_id': response.transaction.id,
            'kind': 'auth',
            'amount': response.amount,
            'currency': response.currency,
            'error': get_error(response),
            'raw_response': get_payment_gateway_response(response),
        }

refund(payment_information, \*\*connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Full or partial return of captured funds to the customer.

Example
"""""""

.. code-block:: python

    def refund(
            payment_information: Dict,
            **connection_params: Dict) -> Dict:

        # Handle connecting to the gateway and sending the refund request here
        response = gateway.refund(token=payment_information['token'])

        # Return a correct response format so Saleor can process it,
        # the response must be json serializable
        return {
            'is_success': response.is_success,
            'transaction_id': response.transaction.id,
            'kind': 'refund',
            'amount': response.amount,
            'currency': response.currency,
            'error': get_error(response),
            'raw_response': get_payment_gateway_response(response),
        }

capture(payment_information, \*\*connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A transfer of the money that was reserved during the authorization stage.

Example
"""""""

.. code-block:: python

    def capture(
            payment_information: Dict,
            **connection_params: Dict) -> Dict:

        # Handle connecting to the gateway and sending the capture request here
        response = gateway.capture(token=payment_information['token'])

        # Return a correct response format so Saleor can process it,
        # the response must be json serializable
        return {
            'is_success': response.is_success,
            'transaction_id': response.transaction.id,
            'kind': 'refund',
            'amount': response.amount,
            'currency': response.currency,
            'error': get_error(response),
            'raw_response': get_payment_gateway_response(response),
        }

void(payment_information, \*\*connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A cancellation of a pending authorization or capture.

Example
"""""""

.. code-block:: python

    def void(
            payment_information: Dict,
            **connection_params: Dict) -> Dict:

        # Handle connecting to the gateway and sending the void request here
        response = gateway.void(token=payment_information['token'])

        # Return a correct response format so Saleor can process it,
        # the response must be json serializable
        return {
            'is_success': response.is_success,
            'transaction_id': response.transaction.id,
            'kind': 'refund',
            'amount': response.amount,
            'currency': response.currency,
            'error': get_error(response),
            'raw_response': get_payment_gateway_response(response),
        }

charge(payment_information, \*\*connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Authorization and capture in a single step.

Example
"""""""

.. code-block:: python

    def charge(
            payment_information: Dict,
            **connection_params: Dict) -> Dict:

        # Handle connecting to the gateway and sending the charge request here
        response = gateway.charge(
            token=payment_information['token'],
            amount=payment_information['amount'])

        # Return a correct response format so Saleor can process it,
        # the response must be json serializable
        return {
            'is_success': response.is_success,
            'transaction_id': response.transaction.id,
            'kind': 'refund',
            'amount': response.amount,
            'currency': response.currency,
            'error': get_error(response),
            'raw_response': get_payment_gateway_response(response),
        }

process_payment(payment_information, \*\*connection_params)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Used for the checkout process, it should perform all the necessary
steps to process a payment. It should use already defined functions,
like authorize and capture.

Example
"""""""

.. code-block:: python

    def process_payment(
            payment_information: Dict,
            **connection_params: Dict) -> Dict:

        # Authorize, update the token, then capture
        authorize_response = authorize(
            payment_information, **connection_params)
        payment_information['token'] = authorize_response['transaction_id']

        capture_response = capture(
            payment_information, **connection_params)

        # Return a list of responses, each response must be json serializable
        return [authorize_response, capture_response]

Parameters
^^^^^^^^^^

+-------------------------+----------+------------------------------------------------------------------------------------+
| name                    | type     | description                                                                        |
+-------------------------+----------+------------------------------------------------------------------------------------+
| ``payment_information`` | ``dict`` | Payment information, containing the tokens, amount, currency and billing.          |
+-------------------------+----------+------------------------------------------------------------------------------------+
| ``connection_params``   | ``dict`` | List of parameters used for connecting to the payment's gateway.                   |
+-------------------------+----------+------------------------------------------------------------------------------------+

Returns
^^^^^^^

+----------------------+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------+
| name                 | type                       | description                                                                                                                              |
+----------------------+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------+
| ``gateway_response`` | ``dict`` or ``list[dict]`` | Dictionary or list of dictionaries containing details about every transaction, with ``is_success`` set to ``True`` if no error occurred. |
+----------------------+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------+
| ``client_token``     | ``str``                    | Unique client's token that will be used as his indentifier in the payment process.                                                       |
+----------------------+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------+

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


Implement get_template()
^^^^^^^^^^^^^^^^^^^^^^^^

Should return a path to a template that will be rendered for the checkout.

Example
"""""""

    .. code-block:: python

        def get_template():
            return 'order/payment/braintree.html'

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

