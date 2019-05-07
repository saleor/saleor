.. _docker-dev:

Using Docker for Development
============================

Using Docker to build software allows you to run and test code without having to worry about external dependencies such as cache servers and databases.

.. warning::

  The following setup is only meant for local development.
  See :ref:`docker-deployment` for production use of Docker.


Local Prerequisites
-------------------

You will need to install `Docker <https://docs.docker.com/install/>`_ and `docker-compose <https://docs.docker.com/compose/install/>`_ before performing the following steps.

.. note::

   Our configuration uses `docker-compose.override.yml <https://docs.docker.com/compose/extends/#understanding-multiple-compose-files>`_ that exposes Saleor, PostgreSQL and Redis ports and runs Saleor via ``python manage.py runserver`` for local development. If you do not wish to use any overrides then you can tell compose to only use `docker-compose.yml` configuration using `-f`, like so `docker-compose -f docker-compose.yml up`.


Using local assets
------------------

By default we do not mount assets for development in the Docker, reason being is those are built in the Docker at build-time
and aren't present in the cloned repository, so what was built on the Docker would be overshadowed by empty directories from the host.

However, we do know that there might be a case that you wish to mount them and see your changes reflected in the container, thus before proceeding you need to modify `docker-compose.override.yml`.

In order for Docker to use your assets from the host, you need to remove ``/app/saleor/static/assets`` volume and add ``./webpack-bundle.json:/app/webpack-bundle.json`` volume.

Additionally if you wish to have the compiled templated emails mounted then you need to also remove ``/app/templates/templated_email/compiled`` volume from web and celery services.


Usage
-----

1. Build the containers using ``docker-compose``

   .. code-block:: bash

    $ docker-compose build


2. Prepare the database

   .. code-block:: bash

    $ docker-compose run --rm web python3 manage.py migrate
    $ docker-compose run --rm web python3 manage.py collectstatic
    $ docker-compose run --rm web python3 manage.py populatedb --createsuperuser

   The ``--createsuperuser`` argument creates an admin account for
   ``admin@example.com`` with the password set to ``admin``.


3. Run the containers

   .. code-block:: bash

    $ docker-compose up


By default, the application is started in debug mode and is configured to listen on port ``8000``.
