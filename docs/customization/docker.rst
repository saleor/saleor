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

   Our configuration uses a ``docker-compose.override.yml`` that exposes PostgreSQL and Redis ports and mounts the host machine code into the containers. 
   If you don't want to expose the ports or if you want to specify your own volumes (eg. in production) you can tell Docker Compose to not include the additional configurations (ports) in the ``docker-compose.override.yml`` file by specifying ``docker-compose.yml`` with the ``-f`` option, as in ``docker-compose -f docker-compose.yml up -d`` and/or by specifying an alternative override file with ``docker-compose -f docker-compose.yml -f docker-compose.alternative-override.yml up -d``

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

   The ``--createsuperuser`` argument creates an admin account for
   ``admin@example.com`` with the password set to ``admin``.


3. Run the containers

   .. code-block:: bash

    $ docker-compose up


By default, the application is started in debug mode and is configured to listen on port ``8000``.
