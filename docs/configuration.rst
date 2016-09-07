Configuration
=============

We are fans of the `12factor <https://12factor.net/>`_ approach and portable code so you can configure most of Saleor using just environment variables.


Environment variables
---------------------

``ALLOWED_HOSTS``
  Controls `Django's allowed hosts <https://docs.djangoproject.com/en/1.10/ref/settings/#allowed-hosts>`_ setting. Defaults to ``localhost``.

``CACHE_URL`` or ``REDIS_URL``
  The URL of a cache database. Defaults to local process memory.

  Redis is recommended. Heroku's Redis will export this setting automatically.

  **Example:** ``redis://redis.example.com:6379/0``

  .. warning::

      If you plan to use more than one WSGI process (or run more than one server/container) you need to use a shared cache server.
      Otherwise each process will have its own version of each user's session which will result in people being logged out and losing their shopping carts.


``DATABASE_URL``
  The URL of the main SQL database. Defaults to an SQLite file.

  PostgreSQL is recommended. Most Heroku databases will export this setting automatically.

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

  Separate multiple values with whitespace.

``SECRET_KEY``
  Controls `Django's secret key <https://docs.djangoproject.com/en/1.10/ref/settings/#secret-key>`_ setting.

Log in using Facebook
---------------------

1. A verified Facebook account is required.
2. You need to `register as a developer <https://developers.facebook.com/>`_ on Facebook and create a new app.
3. You can find *App ID* and *App Secret* in your freshly created app's *Settings* tab.
4. Export ``FACEBOOK_APP_ID`` and ``FACEBOOK_SECRET`` as environment variables with respective app credentials.


Log in using Google
-------------------

1. A Google account is required.
2. First you need to `create a Google Developers Console project and client ID <https://developers.google.com/identity/sign-in/web/devconsole-project>`_.
3. Make sure you provide “Redirect URI” that follows ``http://<yourserver>/account/oauth_callback/google/`` pattern.
4. Obtained “Client ID” and “Client secret“ need to be exported as environment variables: ``GOOGLE_CLIENT_ID`` and ``GOOGLE_CLIENT_SECRET`` respectively.
