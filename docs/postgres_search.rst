PostgreSQL full text search
=============


Installation
------------

No additional external dependency is required to enable PostgreSQL search apart from database itself.

If your server runs on distribution (ex. Ubuntu) that splits postgresql package into base and contrib, both must be installed. Database extension won't work otherwise.


Environment variables
---------------------

PostgreSQL search is enabled by default if Elasticsearch is not configured. No enviroment variable is needed.


Data indexing
-------------

Index is not essential for postgres search and is not configured in Saleor by default. For performance reasons, most likely a `PostgreSQL Gin index <https://www.postgresql.org/docs/current/static/gin.html>`_ should be created on the Product for name and description fields. Reasons for choosing a particular index and configuration strongly depend on particular needs and store size, for each comes with both advantages and limitations. Please read `official PostgreSQL documentation <https://www.postgresql.org/docs/current/static/textsearch-indexes.html>`_ and consider project specifics before making decision.


Search integration architecture
-------------------------------


There are two backend modules defined in `backends <https://github.com/mirumee/saleor/tree/master/saleor/search/backends>`_, one for storefront and one for dashboard search. There is picker module in backends package for picking right backend, depending on configuration.


Testing
-------

Virtually all testing is done in `integration test suite <https://github.com/mirumee/saleor/blob/master/tests/test_postgresql_search.py>`_.
