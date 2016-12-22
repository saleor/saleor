Elasticsearch
=============


Installation
------------

Elasticsearch search backend requires an Elasticsearch server. For development purposes docker-compose will create a Docker container running an Elasticsearch server instance.

Integration can be configured with set of environment variables.
When you're deploying on Heroku - you can use add-on that provides Elasticsearch as a service.
By default Saleor uses Elasticsearch 2.4, but integration is compatibile with Elasticsearch 5 as well
Services available on Heroku:

 - https://elements.heroku.com/addons/searchbox
 - https://elements.heroku.com/addons/bonsai

If you're deploying somewhere else, you can use one of following services:

 - http://www.searchly.com/
 - https://www.elastic.co/cloud


Environment variables
---------------------

``ELASTICSEARCH_URL`` or ``BONSAI_URL`` or ``SEARCHBOX_URL``
  URL to elasticsearch engine. If it's empty - search will be not available.

  **Example:** ``https://user:password@my-3rdparty-es.com:9200``


``ELASTICSEARCH_INDEX_NAME``
  Controls elasticsearch index name where all searchable documents will be stored. Defaults to ``storefront``. Index will be created automatically with first indexing.

Data indexing
-------------

Saleor modified wagtailsearch app from `Wagtail <http://wagtail.io/>`_ to provide search. Core search concepts are preserved, only elasticsearch backends are available.
Dashboard uses custom backend that searches in all available indexes.
Initial search index can be created with following command:

.. code-block:: bash

    $ python manage.py update_index

By default products are reindexed after saving forms in the dashboard. Orders are updated after they're placed.
