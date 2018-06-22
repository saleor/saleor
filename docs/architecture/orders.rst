Order Management
================

Orders are created after customers complete the checkout process. The `Order` object itself contains only general information about the customer's order.


Fulfillment
-----------

The fulfillment represents a group of shipped items with corresponding tracking number. Fulfillments are created by a shop operator to mark selected products in an order as fulfilled.

There are two possible fulfillment statuses:

- ``NEW``
    The default status of newly created fulfillments.

- ``CANCELED``
    The fulfillment canceled by a shop operator. This action is irreversible.


Order statuses
--------------

There are four possible order statuses, based on statuses of its fulfillments:

- ``UNFULFILLED``
    There are no fulfillments related to an order or each one is canceled. An action by a shop operator is required to continue order processing.

- ``PARTIALLY FULFILLED``
    There are some fulfillments with ``FULFILLED`` status related to an order. An action by a shop operator is required to continue order processing.

- ``FULFILLED``
    Each order line is fulfilled in existing fulfillments. Order doesn't require further actions by a shop operator.

- ``CANCELED``
    Order has been canceled. Every fulfillment (if there is any) has ``CANCELED`` status. Order doesn't require further actions by a shop operator.

There is also ``DRAFT`` status, used for orders newly created from dashboard and not yet published.
