Elasticsearch
=============


Installation
------------

Elasticsearch requires separated service enabled (there is a development environment on docker container delivered with saleor).
Integration can be configured with set of environment variables.
Elasticsearch client is installed by default. You may also use external add-ons that deliver elasticsearch service, like Searchbox or Bonsai.

Environment variables
---------------------

``ELASTICSEARCH_URL``
  Contains URL address to the elasticsearch cluster. Defaults to ``http://127.0.0.1:9200/``.

``BONSAI_URL``
  Contains URL to Bonsai elasticsearch add-on on Heroku

``SEARCHBOX_URL``
  Contains URL to Searchbox elasticsearch add-on on Heroku

``ELASTICSEARCH_INDEX_NAME``
  Controls elasticsearch index name where all searchable documents will be stored. Defaults to ``storefront``.

Note that you can only use one Elasticsearch backend at once so if you set ``ELASTICSEARCH_URL`` variable, other URLs will be ignored.

Data indexing
-------------

Saleor uses `django-haystack <http://haystacksearch.org/>`_ to provide search engine, please refer to haystack documentation to get familiar with implementation details.
Initial search indexing can be done with following command:

.. code-block:: bash

    $ python manage.py rebuild_index

By default products are reindexed after saving forms in the dashboard. Orders are updated after they're placed.
