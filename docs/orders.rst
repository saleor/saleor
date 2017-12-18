Order management
================

Orders are created after customers successfully complete the checkout process. The `Order` object itself contains only general information about the customer's order.

Delivery Group
--------------

The delivery group represents a group of ordered items. By default, groups are created along with an order by splitting the cart into parts, depending whether a product requires shipping or not.

Most of the order management actions are taken on the delivery groups and include changing their statuses.

There are three possible delivery group statuses:

- ``NEW``
    The default status of newly created delivery groups.

- ``SHIPPED``
    The delivery group has been marked as shipped.

- ``CANCELLED``
    The delivery group has been cancelled.


Order statuses
--------

Order status is deduced based on statuses of its delivery groups. There are two possible statuses:

- ``OPEN``
    There is at least one delivery group with the ``NEW`` status. An action by a shop operator is required to continue order processing.

- ``CLOSED``
    There are no delivery groups with the ``NEW`` status. Order doesn't require further actions by a shop operator.
