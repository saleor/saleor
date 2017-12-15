Order management
================

Delivery Group
--------------

Delivery group represent parts of an order consisting of multiple order lines. They are created along with order by splitting cart into parts depending whether product has shipping required or not.

Statuses
--------

Order status is deduced based on related delivery group statuses, which in turn can be ``NEW``, ``SHIPPED`` or ``CANCELLED``. For display there are used two values:

- ``OPEN``
    There is at least one delivery group in order having ``NEW`` status.

- ``CLOSED``
    There is no delivery group in order having ``NEW`` status.
