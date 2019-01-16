Stripe (supports Credit Cards)
===========================================

This gateway implements payments using `Stripe <https://stripe.com/>`_.

.. table::

    ================================== ======================================================================================================
    Environment variable               Description
    ================================== ======================================================================================================
    ``STRIPE_PUBLIC_KEY``              Your Stripe public key (test or live)
    ``STRIPE_SECRET_KEY``              Your Stripe secret key (test or live)
    ``STRIPE_STORE_NAME``              Your store name to show in the checkout form
    ``STRIPE_STORE_IMAGE``             An absolute or relative link of your store logo to show in the checkout form
    ``STRIPE_PREFILL``                 Prefill the email adddress in the checkout form if set to ``True`` (default)
    ``STRIPE_REMEMBER_ME``             Add "Remember Me" for future purchases in the checkout form if set to ``True`` (default)
    ``STRIPE_LOCALE``                   Specify ``auto`` to display checkout form in the user's preferred language (default)
    ``STRIPE_ENABLE_BILLING_ADDRESS``  Collect the user's billing address in the checkout form if set to ``True``. The default is ``False``
    ``STRIPE_ENABLE_SHIPPING_ADDRESS`` Collect the user's shipping address in the checkout form if set to ``True``. The default is ``False``
    ================================== ======================================================================================================
