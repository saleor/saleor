Integrations
============

.. _amazon_s3:

Static file and media storage using Amazon S3
---------------------------------------------

If you're using containers for deployment (including Docker and Heroku) you'll want to avoid storing files in the container's volatile filesystem. This integration allows you to delegate storing such files to `Amazon's S3 service <https://aws.amazon.com/s3/>`_.

Set the following environment variables to use S3 to store and serve media files:

``AWS_ACCESS_KEY_ID``
  Your AWS access key.

``AWS_SECRET_ACCESS_KEY``
  Your AWS secret access key.

``AWS_MEDIA_BUCKET_NAME``
  The S3 bucket name to use for media files.

By default static files (such as CSS and JS files required to display your pages) will be served by the application server.

If you intend to use S3 for your static files as well, set an additional environment variable:

``AWS_STATIC_BUCKET_NAME``
  The S3 bucket name to use for static files.


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

To update the exchange rates run the following command at least once per day:

.. code-block:: bash

    $ python manage.py update_exchange_rates --all

.. note::

    Heroku users can use the `Scheduler add-on <https://elements.heroku.com/addons/scheduler>`_ to automatically call the command daily at a predefined time.


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


Send product data to Google Merchant Center
-------------------------------------------

Saleor has tools for generating product feed which can be used with Google Merchant Center. Final file is compressed CSV and saved in location specified by ``saleor.data_feeds.google_merchant.FILE_PATH`` variable.

To generate feed use command:

.. code-block:: bash

    $ python manage.py update_feeds

It's recommended to run this command periodically.

Merchant Center has few country dependent settings, so please validate your feed at Google dashboard. You can also specify there your shipping cost, which is required feed parameter in many countries. More info be found at `Google Support pages <https://support.google.com/merchants>`_.

One of required by Google fields is *brand* attribute. Feed generator checks for it in variant attribute named *brand* or *publisher* (if not, checks in product).

Feed can be downloaded from url: ``http://<yourserver>/feeds/google/``


Full text search with Elasticsearch
-----------------------------------

You can use optional `Elasticsearch <https://www.elastic.co/products/elasticsearch>`_ integration.
To get it working you need to export following environment variable:

``ELASTICSEARCH_URL``
  URL to Elasticsearch server, for example: `"http://localhost:9200"`. Defaults to ``None``

For more details see :doc:`elasticsearch`
