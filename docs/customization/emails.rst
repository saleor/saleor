Customizing Emails
===================


Sending Emails
---------------

Emails are sent with `Django-Templated-Email <https://github.com/vintasoftware/django-templated-email>`_.


Customizing Email Templates
----------------------------

Templates for emails live in ``templates/templated_email``. App-specific directories contain ``*.email`` files that define each specific message type.

The ``source`` directory contains ``*.mjml`` files. Those MJML files are compiled to ``*.html`` and put into ``compiled`` directory.

Emails defined in ``*.email`` files include their HTML versions by referencing the compiled ``*.html`` files.


Compiling MJML
--------------

Source emails use `MJML <https://mjml.io/>`_ and must be compiled to HTML before use.

To compile emails run:

.. code-block:: bash

    $ npm run build-emails
