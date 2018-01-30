Google Analytics
================

Because of EU law regulations, Saleor will not use any tracking cookies by default.

We do however support server-side Google Analytics out of the box using `Google Analytics Measurement Protocol <https://developers.google.com/analytics/devguides/collection/protocol/v1/>`_.

This is implemented using `google-measurement-protocol <https://pypi.python.org/pypi/google-measurement-protocol>`_ and does not use cookies at the cost of not reporting things impossible to track server-side like geolocation and screen resolution.

To get it working you need to export the following environment variable:

``GOOGLE_ANALYTICS_TRACKING_ID``
  Your page's Google “Tracking ID.“
