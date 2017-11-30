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

Index is not essential for postgres search. For performance optimization reasons `PostgreSQL Gin index <https://www.postgresql.org/docs/current/static/gin.html>` is created by default on product model for name and description field. Index usage is transparent to user and no additional action is required for index to stay up to date.


Search integration architecture
-------------------------------


There are two backend modules defined in saleor/search/backends, one for storefront and one for dashboard search. There is picker module in backends package for picking right backend, depending on configuration.


Testing
-------

Virtually all testing is done in `integration test suite <https://github.com/github/saleor/blob/master/saleor/tests/test_postgresql_search.py>`.
