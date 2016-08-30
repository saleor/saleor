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

.. code-block:: bash

    $ npm start

.. warning::

    Files produced this way are not ready for production use.
    To prepare static assets for deployment run:

    .. code-block:: bash

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

.. code-block:: bash

    $ py.test

You can also test against all supported versions of Django and Python.
This is usually only required if you want to contribute your changes back to Saleor.
To do so you can use `Tox <https://tox.readthedocs.io/en/latest/>`_:

.. code-block:: bash

    $ tox


Continuous integration
----------------------

The storefront ships with a working `CircleCI <https://circleci.com/>`_ configuration file.
To use it log into your CircleCI account and enable your repository.


Docker
------

Using Docker to build software allows you to run and test code without having to worry about external dependencies such as cache servers and databases.

.. warning::

  The following setup is only meant for local development.
  See :ref:`docker` for production use of Docker.


Local prerequisites
*******************

You will need to install Docker and
`docker-compose <https://docs.docker.com/compose/install/>`_ before
performing the following steps.


Usage
*****

1. Build the containers using ``docker-compose``

   .. code-block:: bash

    $ docker-compose build


2. Prepare the database

   .. code-block:: bash

    $ docker-compose run web python manage.py migrate
    $ docker-compose run web python manage.py populatedb --createsuperuser

   The ``--createsuperuser`` switch creates an admin account for
    ``admin@example.com`` with the password set to ``admin``.


3. Run the containers

   .. code-block:: bash

    $ docker-compose up


By default, the application is started in debug mode, will automaticall reload code and is configured to listen on port ``8000``.
