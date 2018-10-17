Payments
========

Supported Gateways
------------------

Default configuration uses the *dummy* backend.
It's meant to allow developers to easily simulate different payment results.

Here is a list of supported payment providers:

* Braintree

.. note::

    All payment backends default to using sandbox mode.
    This is very useful for development but make sure you use production mode when deploying to a production server.


Authorisation and Capture
-------------------------

Some of the payment backends support pre-authorising payments.

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
