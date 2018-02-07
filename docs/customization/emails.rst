Customizing Emails
===================


Sending Emails
---------------

Emails are sent with `Django-Templated-Email <https://github.com/vintasoftware/django-templated-email>`_.


Customizing Email Templates
----------------------------

Templates for emails live in ``templates/templated_email`` which has two subdirectories. ``source`` directory contains ``*.email`` and ``*.mjml`` files next to each other, grouped by apps' name. Those MJML files are compiled to ``*.html`` and put into ``compiled`` directory.

Plain emails in ``*.email`` include HTML version by referencing compiled ``*.html`` files.


Compiling MJML
--------------

Source emails use `MJML <https://mjml.io/>`_ and must be compiled to HTML before use.

To compile emails run:

.. code-block:: bash

    $ npm run build-emails
