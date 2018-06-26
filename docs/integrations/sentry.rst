.. _sentry-integration:

Error tracking with Sentry
==========================

Saleor provides integration with `Sentry <https://sentry.io/>`_ - a comprehensive error tracking and reporting tool.

To enable basic error reporting you have to export an environment variable:

``SENTRY_DSN``
  Sentry Data Source Name


If you need to customize the service, please go to the `official Sentry's documentation for Django <https://docs.sentry.io/clients/python/integrations/django/>`_ for more details.
