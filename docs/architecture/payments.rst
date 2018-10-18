Payments
========

Saleor uses the concept of Payment Methods and Transactions to fulfill the payment process.

Payment Methods
---------------

Represents transactable payment information such as credit card details,
gift card information or a customer's authorization to charge their PayPal account.

All payment process related pieces of information are stored at the gateway level,
we are operating on the reusable token which is a unique identifier
of the customer for given gateway.

Payment methods belong to a customer, one can use several payments method within a single order.

Payment method has 3 possible charge statuses:

+----------------+-------------------+------------------------------------------------------------------------------------------------------+
| Code           | GraphQL API value | Description                                                                                          |
+----------------+-------------------+------------------------------------------------------------------------------------------------------+
| charged        | CHARGED           | Funds were taken off the customer founding source, partly or completely covering the payment amount. |
+----------------+-------------------+------------------------------------------------------------------------------------------------------+
| not-charged    | NOT_CHARGED       | No funds were take off the customer founding source yet.                                             |
+----------------+-------------------+------------------------------------------------------------------------------------------------------+
| fully-refunded | FULLY_REFUNDED    | All charged funds were returned to the customer.                                                     |
+----------------+-------------------+------------------------------------------------------------------------------------------------------+

Transactions
------------

Transactions represent attempts to transfer money between your store
and your customers, within a chosen payment method.

There are 5 possible transaction types:

+---------+-------------------+----------------------------------------------------------------------------------------------------------------------------+
| Code    | GraphQL API value | Description                                                                                                                |
+---------+-------------------+----------------------------------------------------------------------------------------------------------------------------+
| auth    | AUTH              | An amount reserved against the customer's funding source. Money does not change hands until the authorization is captured. |
+---------+-------------------+----------------------------------------------------------------------------------------------------------------------------+
| capture | CAPTURE           | A transfer of the money that was reserved during the authorization stage.                                                  |
+---------+-------------------+----------------------------------------------------------------------------------------------------------------------------+
| charge  | CHARGE            | Authorization and capture in a single step.                                                                                |
+---------+-------------------+----------------------------------------------------------------------------------------------------------------------------+
| void    | VOID              | A cancellation of a pending authorization or capture.                                                                      |
+---------+-------------------+----------------------------------------------------------------------------------------------------------------------------+
| refund  | REFUND            | Full or partial return of captured funds to the customer.                                                                  |
+---------+-------------------+----------------------------------------------------------------------------------------------------------------------------+


Supported Gateways
------------------

The default configuration uses the *dummy* backend.
It's meant to allow developers to easily simulate different payment results.

Here is a list of supported payment providers:

* Braintree

.. note::

    All payment backends default to using sandbox mode.
    This is very useful for development but make sure you use production mode when deploying to a production server.


Authorization and Capture
-------------------------

Some of the payment backends support pre-authorizing payments.

Authorization and capture is a two-step process.

Firstly the funds are locked on the payer's account but are not transferred to your bank.

Then depending on the provider and card type you have between a few days and a month to charge the card for an amount not exceeding the authorized amount.

This is very useful when an exact price cannot be determined until after the order is prepared.
It is also useful if your business prefers to manually screen orders for fraud attempts.

When viewing orders with pre-authorized payments Saleor will offer options to either capture or release the funds.


Refunds
-------

You can issue partial or full refunds for all captured payments.
When you edit an order and remove items Saleor will also offer to automatically issue a partial refund.
