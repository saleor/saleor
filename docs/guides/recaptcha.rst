ReCaptcha
=========


Pre-requirements
----------------

You can get your API key set from `Google ReCaptcha
<https://www.google.com/recaptcha/admin>`_.


Enable and Set-up
-----------------

To enable ReCaptcha, you need to set those keys in your environment:

1. ``ENABLE_RECAPTCHA`` to ``True``;
2. ``RECAPTCHA_PUBLIC_KEY`` to your public/ site API key;
3. ``RECAPTCHA_PRIVATE_KEY`` to your secret/ private API key.


.. note::
 You are not required to set your public and private keys for development use.
 You only have to set them up if you are using Saleor for production (Google will remind you if you do not).
