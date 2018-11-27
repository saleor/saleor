.. _payment-gateways:

Supported Payment Gateways
==========================

Here is our list of supported payment gateways, and their configuration:

.. toctree::
   :maxdepth: 1

   payment-gateways/braintree.rst
   payment-gateways/razorpay.rst

The default configuration only uses the `dummy` backend
(see :ref:`how to enable/disable payment gateways <payment_gateways_configuration>`).
It's meant to allow developers to easily simulate different payment results.

For an how-to guide on adding new payments into your Saleor project
please check :ref:`adding-payments`.

.. note::

    All payment backends default to using sandbox mode.
    This is very useful for development but make sure you use production mode when deploying to a production server.
