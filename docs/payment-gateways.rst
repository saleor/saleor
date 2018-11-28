.. _payment-gateways:

Supported Payment Gateways
==========================

Here is our list of supported payment gateways:

.. toctree::
   :maxdepth: 1

   payment-gateways/braintree.rst
   payment-gateways/razorpay.rst

The default configuration uses the `dummy` backend.
It's meant to allow developers to easily simulate different payment results.

For an how-to guide on adding new payments into your Saleor project
please check :ref:`adding-payments`.

.. note::

    All payment backends default to using sandbox mode.
    This is very useful for development but make sure you use production mode when deploying to a production server.

