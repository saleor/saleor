Deployment
==========

.. _docker_deployment:

Docker
------

You will need to install Docker first.

Before building the image make sure you have all of the front-end assets prepared for production:

.. code-block:: bash

 $ npm run build-assets --production
 $ python manage.py collectstatic

Then use Docker to build the image:

.. code-block:: bash

 $ docker build -t mystorefront .


Heroku
------

First steps
***********

.. code-block:: bash

 $ heroku create --buildpack https://github.com/heroku/heroku-buildpack-nodejs.git
 $ heroku buildpacks:add https://github.com/heroku/heroku-buildpack-python.git
 $ heroku addons:create heroku-postgresql:hobby-dev
 $ heroku addons:create heroku-redis:hobby-dev
 $ heroku addons:create sendgrid:starter
 $ heroku addons:create bonsai:sandbox-6 
 $ heroku config:set ALLOWED_HOSTS='<your hosts here>'
 $ heroku config:set NODE_MODULES_CACHE=false
 $ heroku config:set NPM_CONFIG_PRODUCTION=false
 $ heroku config:set SECRET_KEY='<your secret key here>'


.. note::
 Heroku's storage is volatile. This means that all instances of your application will have separate disks and will lose all changes made to the local disk each time the application is restarted. The best approach is to use cloud storage such as Amazon S3. See :ref:`amazon_s3` for configuration details.


Deploy
******

.. code-block:: bash

 $ git push heroku master


Prepare the database
********************

.. code-block:: bash

 $ heroku run python manage.py migrate


Updating currency exchange rates
********************************

This needs to be run periodically. The best way to achieve this is using Heroku's Scheduler service. Let's add it to our application:

.. code-block:: bash

 $ heroku addons:create scheduler

Then log into your Heroku account, find the Heroku Scheduler addon in the active addon list, and have it run the following command on a daily basis:

.. code-block:: bash

 python manage.py update_exchange_rates --all
