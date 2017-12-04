Search
======

There are two possible mechanisms supporting search in Saleor. PostgreSQL full text search capability can be used or external Elasticsearch service.


PostgreSQL full text search
---------------------------

PostgreSQL search in enabled by default, see :doc:`postgres_search` for more information.


Elasticsearch
-------------

You can integrate Saleor with Elasticsearch service, see :doc:`elasticsearch` for more.


Which one to choose
-------------------

Your preference for search backend might depend heavily on project details. PostgreSQL search uses same database as other parts of Saleor, which comes with both pros and cons, making it easy to synchronise content at cost of additional db load. It should be your backend of choice if in doubt as its less complex and easier to maintain. Continue reading on dedicated doc :doc:`postgres_search`.

Elasticsearch service offers a lot of advanced features, such as boosting to tune the relevance of a query or "more like this" queries. See `official website <https://www.elastic.co/products/elasticsearch>`_ to read more about its rich features. To configure elasticsearch in Saleor see :doc:`elasticsearch`.


