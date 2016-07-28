Development
===========

Working with templates
----------------------

Default storefront templates are based on `Bootstrap 3 <http://getbootstrap.com/>`_.

You can find the files under ``/templates/``.


Working with front-end assets
-----------------------------

All static assets live in subdirectories of ``/saleor/static/``.

Stylesheets are written in `Sass <http://sass-lang.com/>`_ and rely on `postcss <http://postcss.org/>`_ and `autoprefixer <https://autoprefixer.github.io/>`_ for cross-browser compatibility.

JavaScript code is written according to the ES2015 standard and relies on `Babel <https://babeljs.io/>`_ for transpilation and browser-specific polyfills.

Everything is compiled together using `webpack module bundler <https://webpack.github.io/>`_.

The resulting files are written to ``/saleor/static/assets/`` and should not be edited manually.

During development it's very convenient to have webpack automatically track changes made locally.
This will also enable *source maps* that are extremely helpful when debugging.

To run webpack in *watch* mode run:

.. code:: bash

    $ npm start

.. warning::

    Files produced this way are not ready for production use.
    To prepare static assets for deployment run:

    .. code:: bash

        $ npm run build-assets


Working with backend code
-------------------------

Python dependencies
~~~~~~~~~~~~~~~~~~~

To guarantee repeatable installations all project dependencies are managed using `pip-tools <https://github.com/nvie/pip-tools>`_.
Project's direct dependencies are listed in ``requirements.in`` and running :code:`pip-compile` generates ``requirements.txt`` that has all versions pinned.

We recommend you use this workflow and keep ``requirements.txt`` under version control to make sure all computers and environments run exactly the same code.


Running tests
-------------

Before you make any permanent changes in the code you should make sure they do not break existing functionality.

The project currently contains very little front-end code so the test suite only covers backend code.

To run backend tests use `pytest <http://docs.pytest.org/en/latest/>`_:

.. code:: bash

    $ py.test

You can also test against all supported versions of Django and Python.
This is usually only required if you want to contribute your changes back to Saleor.
To do so you can use `Tox <https://tox.readthedocs.io/en/latest/>`_:

.. code:: bash

    $ tox
