Braintree (supports PayPal and Credit Cards)
============================================

This gateway implements payments using `Braintree <https://www.braintreepayments.com/>`_.

.. table::

    ========================== =================================================================================
    Environment variable       Description
    ========================== =================================================================================
    ``BRAINTREE_SANDBOX_MODE`` Whether to use a sandbox environment for testing, ``True`` (default) or ``False``
    ``BRAINTREE_MERCHANT_ID``  Merchant ID assigned by Braintree
    ``BRAINTREE_PUBLIC_KEY``   Public key assigned by Braintree
    ``BRAINTREE_PRIVATE_KEY``  Private key assigned by Braintree
    ========================== =================================================================================


.. note::
  This backend does not support fraud detection.
    
.. warning::
  Make sure that Braintree's currency is the same as your shop's, otherwise, customers will be charged the wrong amount.
