Elasticsearch
=============


Installation
------------

Elasticsearch requires separated service enabled (there is a development environment on docker container delivered with saleor).
Integration can be configured with set of environment variables.
Elasticsearch client is installed by default. You may also use external add-ons that deliver elasticsearch service, like Searchbox or Bonsai.

Environment variables
---------------------

``ELASTICSEARCH_URL`` or ``BONSAI_URL`` or ``SEARCHBOX_URL``
  URL to elasticsearch engine. Defaults to WhooshEngine.

  Usage of elasticsearch is recomended. Heroku's add-ons will export this setting automatically.

  **Example:** ``https://user:password@my-3rdparty-es.com:9200``

  .. warning::

      Note that you can only use one Elasticsearch backend at once so if you set ``ELASTICSEARCH_URL`` variable, other URLs will be ignored.

``ELASTICSEARCH_INDEX_NAME``
  Controls elasticsearch index name where all searchable documents will be stored. Defaults to ``storefront``.

Data indexing
-------------

Saleor uses `Haystack <http://haystacksearch.org/>`_ to provide search, please refer to Haystack documentation to get familiar with implementation details.
Initial search indexing can be done with following command:

.. code-block:: bash

    $ python manage.py rebuild_index

By default products are reindexed after saving forms in the dashboard. Orders are updated after they're placed.
