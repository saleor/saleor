.. _payments-architecture:

Payments Architecture
=====================

Authorization and Capture
-------------------------

Some of the payment backends support pre-authorizing payments.

Authorization and capture is a two-step process.

Firstly the funds are locked on the payer's account but are not transferred to your bank.

Then depending on the gateway and the card type, you have between a few days and a month to charge the card for an amount not exceeding the authorized amount.

This is very useful when an exact price cannot be determined until after the order is prepared,
or we want to capture the money as soon as we ship the order.
It is also useful if your business prefers to manually screen orders for fraud attempts.

When viewing orders with pre-authorized payments Saleor will offer options to either capture or void the funds.


Refunds
-------

You can issue partial or full refunds for all captured payments.
When editing an order and removing items, Saleor will also offer to automatically issue a partial refund.

Saleor uses the concept of Payments and Transactions to fulfill the payment process.

Payment Methods
---------------

Represents transactable payment information such as credit card details,
gift card information or a customer's authorization to charge their PayPal account.

All payment process related pieces of information are stored at the gateway level,
we are operating on the reusable token which is a unique identifier
of the customer for given gateway.

Several payment methods can be used within a single order.

Payment has 5 possible charge statuses:

+--------------------+--------------------+---------------------------------------------------------------------------------------------+
| Code               | GraphQL API value  | Description                                                                                 |
+--------------------+--------------------+---------------------------------------------------------------------------------------------+
| not-charged        | NOT_CHARGED        | No funds were take off the customer's funding source yet.                                   |
+--------------------+--------------------+---------------------------------------------------------------------------------------------+
| partially-charged  | PARTIALLY_CHARGED  | Funds were taken off the customer's funding source, partly covering the payment amount.     |
+--------------------+--------------------+---------------------------------------------------------------------------------------------+
| fully-charged      | FULLY_CHARGED      | Funds were taken off the customer's funding source, completely covering the payment amount. |
+--------------------+--------------------+---------------------------------------------------------------------------------------------+
| partially-refunded | PARTIALLY_REFUNDED | Part of charged funds were returned to the customer.                                        |
+--------------------+--------------------+---------------------------------------------------------------------------------------------+
| fully-refunded     | FULLY_REFUNDED     | All charged funds were returned to the customer.                                            |
+--------------------+--------------------+---------------------------------------------------------------------------------------------+

Transactions
------------

Transaction represent attempts to transfer money between your store
and your customers, within a chosen payment method.

There are 5 possible transaction kinds:

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

Transaction errors
------------------

Saleor unifies error codes across all gateways.

+---------------------+---------------------+----------------------------------------------------+
| Code                | Graphql API value   | Description                                        |
+---------------------+---------------------+----------------------------------------------------+
| incorrect_number    | INCORRECT_NUMBER    | Incorrect card number                              |
+---------------------+---------------------+----------------------------------------------------+
| invalid_number      | INVALID_NUMBER      | Invalid card number                                |
+---------------------+---------------------+----------------------------------------------------+
| incorrect_cvv       | INCORRECT_CVV       | Incorrect CVV (or CVC)                             |
+---------------------+---------------------+----------------------------------------------------+
| invalid_cvv         | INVALID_CVV         | Invalid CVV (or CVC)                               |
+---------------------+---------------------+----------------------------------------------------+
| incorrect_zip       | INCORRECT_ZIP       | Incorrect postal code                              |
+---------------------+---------------------+----------------------------------------------------+
| incorrect_address   | INCORRECT_ADDRESS   | Incorrect address (excluding postal code)          |
+---------------------+---------------------+----------------------------------------------------+
| invalid_expiry_date | INVALID_EXPIRY_DATE | Incorrect card's expiration date                   |
+---------------------+---------------------+----------------------------------------------------+
| expired             | EXPIRED             | Expired payment's method token                     |
+---------------------+---------------------+----------------------------------------------------+
| declined            | DECLINED            | Transaction was declined by the gateway            |
+---------------------+---------------------+----------------------------------------------------+
| processing_error    | PROCESSING_ERROR    | Default error used for all cases not covered above |
+---------------------+---------------------+----------------------------------------------------+
