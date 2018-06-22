.. _settings_configuration:

Configuration
=============

We are fans of the `12factor <https://12factor.net/>`_ approach and portable code so you can configure most of Saleor using just environment variables.


Environment variables
---------------------

``ALLOWED_HOSTS``
  Controls `Django's allowed hosts <https://docs.djangoproject.com/en/1.10/ref/settings/#allowed-hosts>`_ setting. Defaults to ``localhost``.

  Separate multiple values with comma.

``CACHE_URL`` or ``REDIS_URL``
  The URL of a cache database. Defaults to local process memory.

  Redis is recommended. Heroku's Redis will export this setting automatically.

  **Example:** ``redis://redis.example.com:6379/0``

  .. warning::

      If you plan to use more than one WSGI process (or run more than one server/container) you need to use a shared cache server.
      Otherwise each process will have its own version of each user's session which will result in people being logged out and losing their shopping carts.


``DATABASE_URL``
  Defaults to a local PostgreSQL instance. See :ref:`docker-dev` for how to get a local database running inside a Docker container.

  Most Heroku databases will export this setting automatically.

  **Example:** ``postgres://user:password@psql.example.com/database``

``DEBUG``
  Controls `Django's debug mode <https://docs.djangoproject.com/en/1.10/ref/settings/#debug>`_. Defaults to ``True``.

``DEFAULT_FROM_EMAIL``
  Default email address to use for outgoing mail.

``EMAIL_URL``
  The URL of the email gateway. Defaults to printing everything to the console.

  **Example:** ``smtp://user:password@smtp.example.com:465/?ssl=True``

``INTERNAL_IPS``
  Controls `Django's internal IPs <https://docs.djangoproject.com/en/1.10/ref/settings/#internal-ips>`_ setting. Defaults to ``127.0.0.1``.

  Separate multiple values with comma.

``SECRET_KEY``
  Controls `Django's secret key <https://docs.djangoproject.com/en/1.10/ref/settings/#secret-key>`_ setting.

``SENTRY_DSN``
  Sentry's `Data Source Name <https://docs.sentry.io/quickstart/#about-the-dsn>`_. Disabled by default, allows to enable integration with Sentry (see :ref:`sentry-integration` for details).

``MAX_CART_LINE_QUANTITY``
  Controls maximum number of items in one cart line. Defaults to ``50``.

``STATIC_URL``
  Controls production assets' mount path. Defaults to ``/static/assets/``.

``VATLAYER_ACCESS_KEY``
  Access key to `vatlayer API <https://vatlayer.com/>`_. Enables VAT support within European Union.

  To update the tax rates run the following command at least once per day:

  .. code-block:: console

   $ python manage.py get_vat_rates

``DEFAULT_CURRENCY``
  Controls all prices entered and stored in the store as this single default currency (for more information, see :ref:`money_architecture`).

``DEFAULT_COUNTRY``
  Sets the default country for the store. It controls the default VAT to be shown if required, the default shipping country, etc.
