Integrations
============

Converting prices to local currencies using Open Exchange Rates
---------------------------------------------------------------

This integration will allow your customers to see product prices in their local currencies.
Local prices are only provided as an estimate, customers are still charged in your store's default currency.

Before you begin you will need an `Open Exchange Rates account <https://openexchangerates.org/>`_.
Unless you need to update the exchange rates multiple times a day the free Subscription Plan should be enough but do consider paying for the wonderful service that Open Exchange Rates provides.
Start by signing up and creating an “App ID”.

Export the following environment variable:

``OPENEXCHANGERATES_API_KEY``
  Your store's Open Exchange Rates “App ID.”


Log in using Facebook
---------------------

This integration will let your customers log in using their Facebook accounts.

Before you begin you will need a verified Facebook account.
Start by `registering as a developer <https://developers.facebook.com/>`_ on Facebook and creating a new Facebook app for your store.

You can find your freshly created app's “App ID” and “App Secret” in its *Settings* tab.

Export the following environment variables:

``FACEBOOK_APP_ID``
  Your Facebook app's “App ID.”

``FACEBOOK_SECRET``
  Your Facebook app's “App Secret.”


Log in using Google
-------------------

This integration will let your customers log in using their Google accounts.

Before you begin you will need a Google account.
Start by `creating a Google Developers Console project and client ID <https://developers.google.com/identity/sign-in/web/devconsole-project>`_.

Set the “Redirect URI” to ``http://<yourserver>/account/oauth_callback/google/`` where ``<yourserver>`` is the domain that you use.

Obtained “Client ID” and “Client secret“ need to be exported as environment variables:

``GOOGLE_CLIENT_ID``
  Your project's “Client ID.”

``GOOGLE_CLIENT_SECRET``
  Your project's “Client secret.“


Reporting with Google Analytics
-------------------------------

Because of EU law regulations, Saleor will not use any tracking cookies by default.

We do however support server-side Google Analytics out of the box using `Google Analytics Measurement Protocol <https://developers.google.com/analytics/devguides/collection/protocol/v1/>`_.

This is implemented using `google-measurement-protocol <https://pypi.python.org/pypi/google-measurement-protocol>`_ and does not use cookies at the cost of not reporting things impossible to track server-side like geolocation and screen resolution.

To get it working you need to export the following environment variable:

``GOOGLE_ANALYTICS_TRACKING_ID``
  Your page's Google “Tracking ID.“
