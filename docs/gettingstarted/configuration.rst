.. _settings_configuration:

Configuration
=============

We are fans of the `12factor <https://12factor.net/>`_ approach and portable code so you can configure most of Saleor using just environment variables.


Environment variables
---------------------

``ALLOWED_HOSTS``
  Controls `Django's allowed hosts <https://docs.djangoproject.com/en/2.1/ref/settings/#s-allowed-hosts>`_ setting. Defaults to ``localhost``.

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
  Controls `Django's debug mode <https://docs.djangoproject.com/en/2.1/ref/settings/#s-debug>`_. Defaults to ``True``.

``DEFAULT_FROM_EMAIL``
  Default email address to use for outgoing mail.

``EMAIL_URL``
  The URL of the email gateway. Defaults to printing everything to the console.

  **Example:** ``smtp://user:password@smtp.example.com:465/?ssl=True``

``INTERNAL_IPS``
  Controls `Django's internal IPs <https://docs.djangoproject.com/en/2.1/ref/settings/#s-internal-ips>`_ setting. Defaults to ``127.0.0.1``.

  Separate multiple values with comma.

``SECRET_KEY``
  Controls `Django's secret key <https://docs.djangoproject.com/en/2.1/ref/settings/#s-secret-key>`_ setting.

``SENTRY_DSN``
  Sentry's `Data Source Name <https://docs.sentry.io/quickstart/#about-the-dsn>`_. Disabled by default, allows to enable integration with Sentry (see :ref:`sentry-integration` for details).

``MAX_CART_LINE_QUANTITY``
  Controls maximum number of items in one cart line. Defaults to ``50``.

``STATIC_URL``
  Controls production assets' mount path. Defaults to ``/static/``.

``VATLAYER_ACCESS_KEY``
  Access key to `vatlayer API <https://vatlayer.com/>`_. Enables VAT support within European Union.

  To update the tax rates run the following command at least once per day:

  .. code-block:: console

   $ python manage.py get_vat_rates

``DEFAULT_CURRENCY``
  Controls all prices entered and stored in the store as this single default currency (for more information, see :ref:`money_architecture`).

``DEFAULT_COUNTRY``
  Sets the default country for the store. It controls the default VAT to be shown if required, the default shipping country, etc.

``TIME_ZONE``
  Sets the time zone. Defaults to `UTC`.
  Further `documentation <https://docs.djangoproject.com/en/2.1/ref/settings/#time-zone>`_


``LANGUAGE_CODE``
  Sets the language. Defaults to `en`.
  Further `documentation <https://docs.djangoproject.com/en/2.1/ref/settings/#language-code>`_

``USE_I18N``
  Whether or not to enable Djangos translation system I18N. Defaults to `True`.
  Further `documentation https://docs.djangoproject.com/en/2.1/ref/settings/#use-i18n>`_

``USE_L10N``
  Whether or not to use localization - eg date formatting. Defaults to `True`.
  Further `documentation https://docs.djangoproject.com/en/2.1/ref/settings/#use-l10n>`_

``USE_TZ``
  Enable or disable timezone awareness. Defaults to `True`.
  Further `documentation <https://docs.djangoproject.com/en/2.1/ref/settings/#std:setting-USE_TZ>`_

Logging and handler levels:

``ROOT_LOG_LEVEL`` - The 'root' log level, defaults to 'INFO'.
``MAIL_ADMINS_HANDLER_LEVEL`` - The mail admin handler log level, defaults to `ERROR`.
``CONSOLE_HANDLER_LEVEL`` - The console handler log level, defaults to `DEBUG`.
``DJANGO_LOG_LEVEL`` - The django log level, defaults to `INFO`.
``DJANGO_SERVER_LOG_LEVEL`` - The django.server log level, defaults to `INFO`.
``SALEOR_LOG_LEVEL`` - The saleor log level, defaults to `DEBUG`.

Further documentation on logging can be found
`here <https://docs.djangoproject.com/en/2.1/topics/logging/#module-django.utils.log>`_

``AVAILABLE_CURRENCIES``
  A comma separated list of the currencies to be available for selection.

``ACCOUNT_ACTIVATION_DAYS``
  Defaults to `3`.

``LOGIN_REDIRECT_URL``
  The relative url to redirect a user after unsuccessful login attempts. Defaults to `home`.

``LOW_STOCK_THRESHOLD``
  The level of stock for a product line under which it will be marked as low stock. Defaults to `10`.

``MAX_CART_LINE_QUANTITY``
  Maximum number of items of a product line allowed to be added to the cart. Defaults to `50`.

``PAGINATE_BY``
  Number of products per page to display in the store front. Defaults to `16`.

``DASHBOARD_PAGINATE_BY``
  Number of products per page to display in the admin dashboard. Defaults to `30`.

``DASHBOARD_SEARCH_LIMIT``
  Number of search results to display after a product search. Defaults to `5`.

Placeholder images:
``PLACEHOLDER_IMAGE_60`` - The relative path of the 60 x 60 placeholder image. Defaults to `images/placeholder60x60.png`.
``PLACEHOLDER_IMAGE_120`` - The relative path of the 120 x 120 placeholder image. Defaults to `images/placeholder120x120.png`.
``PLACEHOLDER_IMAGE_255`` - The relative path of the 255 x 255 placeholder image. Defaults to `images/placeholder255x255.png`.
``PLACEHOLDER_IMAGE_540`` - The relative path of the 540 x 540 placeholder image. Defaults to `images/placeholder540x540.png`.
``PLACEHOLDER_IMAGE_1080`` - The relative path of the 1080 x 1080 placeholder image. Defaults to `images/placeholder1080x1080.png`.
``DEFAULT_PLACEHOLDER`` - The default placeholder value. Defaults to the `PLACEHOLDER_IMAGE_255` value.

``LOGOUT_ON_PASSWORD_CHANGE``
  Whether one should be logged out after changing one's password. Defaults to `False`.

``DB_SEARCH_ENABLED``
  Enable the product search feature on the storefront. Defaults to `True`.
