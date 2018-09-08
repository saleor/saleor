.. _docker-dev:

Using Docker for Development
============================

Using Docker to build software allows you to run and test code without having to worry about external dependencies such as cache servers and databases.

.. warning::

  The following setup is only meant for local development.
  See :ref:`docker-deployment` for production use of Docker.


Local Prerequisites
-------------------

You will need to install Docker and `docker-compose <https://docs.docker.com/compose/install/>`_ before performing the following steps.

.. note::

   Our configuration exposes PostgreSQL, Redis and Elasticsearch ports. If you have problems running this docker file because of port conflicts, you can remove ``ports`` section from ``docker-compose.yml``.


Usage
-----

1. Build the containers using ``docker-compose``

   .. code-block:: bash

    $ docker-compose build


2. Prepare the database

   .. code-block:: bash

    $ docker-compose run web python3 manage.py migrate
    $ docker-compose run web python3 manage.py collectstatic
    $ docker-compose run web python3 manage.py populatedb --createsuperuser

   The ``--createsuperuser`` switch creates an admin account for
   ``admin@example.com`` with the password set to ``admin``.


3. Run the containers

   .. code-block:: bash

    $ docker-compose up


By default, the application is started in debug mode, will automatically reload code and is configured to listen on port ``8000``.


