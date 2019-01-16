Razorpay (supports only the paisa currency)
===========================================

This gateway implements payments using `Razorpay <https://razorpay.com/>`_.

First of all, to create your API credentials, you need to go in your Razorpay account settings,
then in the `API Keys section <https://dashboard.razorpay.com/#/app/keys>`_.

.. table::

    ========================== =========================================================================
    Environment variable       Description
    ========================== =========================================================================
    ``RAZORPAY_PUBLIC_KEY``    Your Razorpay **key id**
    ``RAZORPAY_SECRET_KEY``    Your Razorpay **secret key id**
    ``RAZORPAY_PREFILL``       Pre-fill the email and customer's full name if set to ``True`` (default)
    ``RAZORPAY_STORE_NAME``    Your store name
    ``RAZORPAY_STORE_IMAGE``   An absolute or relative link to your store logo
    ========================== =========================================================================


.. warning::

    Only the paisa (INR) currency is supported by Razorpay as of now.
