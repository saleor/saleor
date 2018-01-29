Payments
========


Supported Gateways
------------------

Saleor uses `django-payments <http://django-payments.readthedocs.io/en/latest/>`_ library to process payments.

Default configuration uses the *dummy* backend.
It's meant to allow developers to easily simulate different payment results.

Here is a list of supported payment providers:

* Authorize.Net
* Braintree
* Coinbase
* Cybersource
* Dotpay
* Google Wallet
* PayPal
* Sage Pay
* Sofort.com
* Stripe

Please note that this list is only provided here for reference.
Please consult `django-payments documentation <http://django-payments.readthedocs.io/en/latest/modules.html>`_ for an up to date list and instructions.

.. note::

    All payment backends default to using sandbox mode.
    This is very useful for development but make sure you use production mode when deploying to a production server.


3-D Secure
----------

3-D Secure is a card protection protocol that allows merchants to partially mitigate fraud responsibility.
In practice it greatly lowers the probability of a chargeback.

Saleor supports 3-D Secure but whether it's used depends on the payment processor and the card being used.


Fraud Protection
----------------

Some of the payment backends provide automatic fraud protection heuristics.
If such information is available Saleor will show it in the order management panel.


Authorisation and Capture
-------------------------

Some of the payment backends support pre-authorising payments.
Please see `django-payments documentation <http://django-payments.readthedocs.io/en/latest/preauth.html>`_ for details.

Authorisation and capture is a two step process.

First the funds are locked on the payer's account but are not transferred to your bank.

Then depending on the provider and card type you have between a few days and a month to charge the card for an amount not exceeding the authorised amount.

This is very useful when an exact price cannot be determined until after the order is prepared.
It is also useful if your business prefers to manually screen orders for fraud attempts.

When viewing orders with pre-authorised payments Saleor will offer options to either capture or release the funds.


Refunds
-------

You can issue partial or full refunds for all captured payments.
When you edit an order and remove items Saleor will also offer to automatically issue a partial refund.
