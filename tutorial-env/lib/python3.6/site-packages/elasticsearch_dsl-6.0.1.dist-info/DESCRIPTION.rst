Elasticsearch DSL
=================

Elasticsearch DSL is a high-level library whose aim is to help with writing and
running queries against Elasticsearch. It is built on top of the official
low-level client (`elasticsearch-py <https://github.com/elastic/elasticsearch-py>`_).

It provides a more convenient and idiomatic way to write and manipulate
queries. It stays close to the Elasticsearch JSON DSL, mirroring its
terminology and structure. It exposes the whole range of the DSL from Python
either directly using defined classes or a queryset-like expressions.

It also provides an optional wrapper for working with documents as Python
objects: defining mappings, retrieving and saving documents, wrapping the
document data in user-defined classes.

To use the other Elasticsearch APIs (eg. cluster health) just use the
underlying client.

Installation
------------

::

  pip install elasticsearch-dsl


Compatibility
-------------

The library is compatible with all Elasticsearch versions since ``1.x`` but you
**have to use a matching major version**:

For **Elasticsearch 6.0** and later, use the major version 5 (``6.x.y``) of the
library.

For **Elasticsearch 5.0** and later, use the major version 5 (``5.x.y``) of the
library.

For **Elasticsearch 2.0** and later, use the major version 2 (``2.x.y``) of the
library.


The recommended way to set your requirements in your `setup.py` or
`requirements.txt` is::

    # Elasticsearch 6.x
    elasticsearch-dsl>=6.0.0,<7.0.0

    # Elasticsearch 5.x
    elasticsearch-dsl>=5.0.0,<6.0.0

    # Elasticsearch 2.x
    elasticsearch-dsl>=2.0.0,<3.0.0


The development is happening on ``master``, ``2.x``, and ``1.x`` branches, respectively.

Search Example
--------------

Let's have a typical search request written directly as a ``dict``:

.. code:: python

    from elasticsearch import Elasticsearch
    client = Elasticsearch()

    response = client.search(
        index="my-index",
        body={
          "query": {
            "bool": {
              "must": [{"match": {"title": "python"}}],
              "must_not": [{"match": {"description": "beta"}}],
              "filter": [{"term": {"category": "search"}}]
            }
          },
          "aggs" : {
            "per_tag": {
              "terms": {"field": "tags"},
              "aggs": {
                "max_lines": {"max": {"field": "lines"}}
              }
            }
          }
        }
    )

    for hit in response['hits']['hits']:
        print(hit['_score'], hit['_source']['title'])

    for tag in response['aggregations']['per_tag']['buckets']:
        print(tag['key'], tag['max_lines']['value'])



The problem with this approach is that it is very verbose, prone to syntax
mistakes like incorrect nesting, hard to modify (eg. adding another filter) and
definitely not fun to write.

Let's rewrite the example using the Python DSL:

.. code:: python

    from elasticsearch import Elasticsearch
    from elasticsearch_dsl import Search

    client = Elasticsearch()

    s = Search(using=client, index="my-index") \
        .filter("term", category="search") \
        .query("match", title="python")   \
        .exclude("match", description="beta")

    s.aggs.bucket('per_tag', 'terms', field='tags') \
        .metric('max_lines', 'max', field='lines')

    response = s.execute()

    for hit in response:
        print(hit.meta.score, hit.title)

    for tag in response.aggregations.per_tag.buckets:
        print(tag.key, tag.max_lines.value)

As you see, the library took care of:

  * creating appropriate ``Query`` objects by name (eq. "match")

  * composing queries into a compound ``bool`` query

  * putting the ``term`` query in a filter context of the ``bool`` query

  * providing a convenient access to response data

  * no curly or square brackets everywhere


Persistence Example
-------------------

Let's have a simple Python class representing an article in a blogging system:

.. code:: python

    from datetime import datetime
    from elasticsearch_dsl import DocType, Date, Integer, Keyword, Text, connections

    # Define a default Elasticsearch client
    connections.create_connection(hosts=['localhost'])

    class Article(DocType):
        title = Text(analyzer='snowball', fields={'raw': Keyword()})
        body = Text(analyzer='snowball')
        tags = Keyword()
        published_from = Date()
        lines = Integer()

        class Meta:
            index = 'blog'

        def save(self, ** kwargs):
            self.lines = len(self.body.split())
            return super(Article, self).save(** kwargs)

        def is_published(self):
            return datetime.now() > self.published_from

    # create the mappings in elasticsearch
    Article.init()

    # create and save and article
    article = Article(meta={'id': 42}, title='Hello world!', tags=['test'])
    article.body = ''' looong text '''
    article.published_from = datetime.now()
    article.save()

    article = Article.get(id=42)
    print(article.is_published())

    # Display cluster health
    print(connections.get_connection().cluster.health())


In this example you can see:

  * providing a default connection

  * defining fields with mapping configuration

  * setting index name

  * defining custom methods

  * overriding the built-in ``.save()`` method to hook into the persistence
    life cycle

  * retrieving and saving the object into Elasticsearch

  * accessing the underlying client for other APIs

You can see more in the persistence chapter of the documentation.

Migration from ``elasticsearch-py``
-----------------------------------

You don't have to port your entire application to get the benefits of the
Python DSL, you can start gradually by creating a ``Search`` object from your
existing ``dict``, modifying it using the API and serializing it back to a
``dict``:

.. code:: python

    body = {...} # insert complicated query here

    # Convert to Search object
    s = Search.from_dict(body)

    # Add some filters, aggregations, queries, ...
    s.filter("term", tags="python")

    # Convert back to dict to plug back into existing code
    body = s.to_dict()

Development
-----------

Activate Virtual Environment (`virtualenvs <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_):

.. code:: bash

    $ virtualenv venv
    $ source venv/bin/activate

To install all of the dependencies necessary for development, run:

.. code:: bash

    $ pip install -e '.[develop]'

To run all of the tests for ``elasticsearch-dsl-py``, run:

.. code:: bash

    $ python setup.py test

Alternatively, it is possible to use the ``run_tests.py`` script in
``test_elasticsearch_dsl``, which wraps `pytest
<http://doc.pytest.org/en/latest/>`_, to run subsets of the test suite. Some
examples can be seen below:

.. code:: bash

    # Run all of the tests in `test_elasticsearch_dsl/test_analysis.py`
    $ ./run_tests.py test_analysis.py

    # Run only the `test_analyzer_serializes_as_name` test.
    $ ./run_tests.py test_analysis.py::test_analyzer_serializes_as_name

``pytest`` will skip tests from ``test_elasticsearch_dsl/test_integration``
unless there is an instance of Elasticsearch on which a connection can occur.
By default, the test connection is attempted at ``localhost:9200``, based on
the defaults specified in the ``elasticsearch-py`` `Connection
<https://github.com/elastic/elasticsearch-py/blob/master/elasticsearch
/connection/base.py#L29>`_ class. **Because running the integration
tests will cause destructive changes to the Elasticsearch cluster, only run
them when the associated cluster is empty.** As such, if the
Elasticsearch instance at ``localhost:9200`` does not meet these requirements,
it is possible to specify a different test Elasticsearch server through the
``TEST_ES_SERVER`` environment variable.

.. code:: bash

    $ TEST_ES_SERVER=my-test-server:9201 ./run_tests

Documentation
-------------

Documentation is available at https://elasticsearch-dsl.readthedocs.io.

Contribution Guide
------------------

Want to hack on Elasticsearch DSL? Awesome! We have `Contribution-Guide <https://github.com/elastic/elasticsearch-dsl-py/blob/master/CONTRIBUTING.rst>`_.

License
-------

Copyright 2013 Elasticsearch

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

