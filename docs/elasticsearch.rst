Elasticsearch
=============


Installation
------------

Elasticsearch requires separated service enabled (there is a development environment on docker container delivered with saleor).
Integration can be configured with set of environment variables.
You have to install elasticsearch client library before you start using this integration:

.. code-block:: bash

    $ pip install elasticsearch


Environment variables
---------------------

``ELASTICSEARCH_URL``
  Contains URL address to the elasticsearch cluster. Defaults to ``http://127.0.0.1:9200/``.

``ELASTICSEARCH_INDEX_NAME``
  Controls elasticsearch index name where all searchable documents will be stored. Defaults to ``saleor``.



Data indexing
-------------

Saleor uses `django-haystack <http://haystacksearch.org/>`_ to provide search engine, please refer to haystack documentation to get familiar with implementation details.
Initial search indexing can be done with following command:

.. code-block:: bash

    $ python manage.py rebuild_index

By default products are reindexed after saving forms in the dashboard. Orders are updated after they're placed.
