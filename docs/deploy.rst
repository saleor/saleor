Deployment
==========

Docker
------


Local prerequisites
*******************

You will need to install Docker and
`docker-compose <https://docs.docker.com/compose/install/>`__ before
performing the following steps.

Usage
*****

1. Build ``Saleor`` with ``docker-compose``

   .. code::

    $ docker-compose build

2. Prepare the database

   .. code::

    $ docker-compose run web python manage.py migrate
    $ docker-compose run web python manage.py populatedb --createsuperuser

   The ``--createsuperuser`` switch creates an admin account for
    ``admin@example.com`` with the password set to ``admin``.

3. Install front-end dependencies

   .. code::

    $ docker-compose run web npm install
    $ docker-compose run web grunt

4. Run ``Saleor``

   .. code::

    $ docker-compose up

By default, the application is configured to listen on port ``8000``.


Heroku
------

First steps
***********

.. code::

 $ heroku create --buildpack https://github.com/ddollar/heroku-buildpack-multi.git
 $ heroku addons:add heroku-postgresql
 $ heroku addons:add heroku-redis
 $ heroku config:set SECRET_KEY='<your secret key here>'
 $ heroku config:set ALLOWED_HOSTS='<your hosts here>'


.. note::
 Heroku's storage is volatile. This means that all instances of your application will have separate disks and will lose all changes made to the local disk each time the application is restarted. The best approach is to use cloud storage such as [[Amazon S3|Storage: Amazon S3]].

Deploy
******

.. code::

 $ git push heroku master


Prepare the database
********************

.. code::

 $ heroku run python manage.py migrate
