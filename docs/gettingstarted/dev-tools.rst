Debug tools
===========

We have built in support for some of the debug tools.

Django debug toolbar
--------------------

`Django Debug Toolbar <https://github.com/jazzband/django-debug-toolbar>`_ is turned on if Django is running in debug mode.

Silk
----

Silk's presence can be controled via environmental variable

``ENABLE_SILK``
  Controls `django-silk <https://github.com/jazzband/django-silk>`_. Defaults to ``False``

#. Set environment variable.

   .. code-block:: console

    $ export ENABLE_SILK='True'

#. Install packages from requirements_dev.txt:

   .. code-block:: console

    $ python -m pip install -r requirements_dev.txt

#. Restart server

