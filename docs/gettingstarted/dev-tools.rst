Debug tools
===========

We have built in support for some debug tools, turned off by default.
You can control them with environmental variables:

``ENABLE_DEBUG_TOOLBAR``
  Controls `django-debug-toolbar <https://github.com/jazzband/django-debug-toolbar>`. Defaults to ``False``

``ENABLE_SILK``
  Controls `django-silk <https://github.com/jazzband/django-silk>`. Defaults to ``False``


Enabling Silk
-----------------------------
#. Set environment variable.

   .. code-block:: console

    $ export ENABLE_SILK='True'

#. Install packages from requirements_dev.txt:

   .. code-block:: console

    $ python -m pip install -r requirements_dev.txt

#. Restart server

