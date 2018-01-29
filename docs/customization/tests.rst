Running Tests
=============

Before you make any permanent changes in the code you should make sure they do not break existing functionality.

The project currently contains very little front-end code so the test suite only covers backend code.

To run backend tests use `pytest <http://docs.pytest.org/en/latest/>`_:

.. code-block:: bash

    $ py.test

You can also test against all supported versions of Django and Python.
This is usually only required if you want to contribute your changes back to Saleor.
To do so you can use `Tox <https://tox.readthedocs.io/en/latest/>`_:

.. code-block:: bash

    $ tox
