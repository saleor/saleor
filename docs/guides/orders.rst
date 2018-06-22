Orders
======

Saleor gives a possibility to manage orders from dashboard. It can be done in dashboard ``Orders`` tab.


Draft orders
------------

To create draft order, first you must go to dashboard ``Orders`` tab and choose circular **+** button visible above the list of existing orders.

Those orders can be fully edited until confirmed by clicking `Create order`. You can modify ordered items, customer (also just set an email), billing and shipping address, shipping method and discount. Any voucher you apply will cause automatic order recalculation to fit actual state of an order every time it changes.

Confirming an order by clicking `Create order` will change status to unfulfilled and disable most of the edit actions. You can optionally notify customer - if attached any - about that order by sending email.


Marking orders as paid
----------------------

You can manually mark orders as paid if needed in order details page. This option is visible only for unpaid orders as an action in `Payments` card.

.. warning::

  You won't be able to refund a payment handled manually. This is due to lack of enough data required to handle transaction.
