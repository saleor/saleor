Social features
===============

Some of the social features require additional prerequisites to work.


Log in using Facebook
---------------------

1. A verified Facebook account is required.
2. You need to `register as a developer <https://developers.facebook.com/>`_ on Facebook and create a new app.
3. You can find *App ID* and *App Secret* in your freshly created app's *Settings* tab.
4. Export ``FACEBOOK_APP_ID`` and ``FACEBOOK_SECRET`` as environmental variables with respective app credentials.


Log in using Google
-------------------

1. A Google account is required.
2. First you need to `create a Google Developers Console project and client ID <https://developers.google.com/identity/sign-in/web/devconsole-project>`_.
3. Make sure you provide “Redirect URI” that follows ``http://<yourserver>/account/oauth_callback/google/`` pattern.
4. Obtained “Client ID” and “Client secret“ need to be exported as environment variables: ``GOOGLE_CLIENT_ID`` and ``GOOGLE_CLIENT_SECRET`` respectively.
