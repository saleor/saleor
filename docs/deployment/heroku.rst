Heroku
======

Configuration
-------------

Within the repo, git should already be initialized. All you have to do now is add the `heroku` remote with your `app-name`

.. code-block:: console

 $ heroku git:remote -a 'app-name'
 $ heroku buildpacks:set heroku/nodejs
 $ heroku buildpacks:add heroku/python
 $ heroku addons:create heroku-postgresql:hobby-dev
 $ heroku addons:create heroku-redis:hobby-dev
 $ heroku addons:create sendgrid:starter
 $ heroku config:set ALLOWED_HOSTS='<your hosts here>'
 $ heroku config:set NODE_MODULES_CACHE=false
 $ heroku config:set NPM_CONFIG_PRODUCTION=false
 $ heroku config:set SECRET_KEY='<your secret key here>'


.. note::
 Heroku's storage is volatile. This means that all instances of your application will have separate disks and will lose all changes made to the local disk each time the application is restarted. The best approach is to use cloud storage such as Amazon S3. See :ref:`amazon-s3` for configuration details.


Deployment
----------

.. code-block:: console

 $ git push heroku master


Preparing the Database
----------------------

.. code-block:: console

 $ heroku run python manage.py migrate


Updating Currency Exchange Rates
--------------------------------

This needs to be run periodically. The best way to achieve this is using Heroku's Scheduler service. Let's add it to our application:

.. code-block:: console

 $ heroku addons:create scheduler

Then log into your Heroku account, find the Heroku Scheduler addon in the active addon list, and have it run the following command on a daily basis:

.. code-block:: console

 $ python manage.py update_exchange_rates --all


Enabling Elasticsearch
----------------------

By default, Saleor uses Postgres as a search backend, but if you want to switch to Elasticsearch, it can be easily achieved using the Bonsai plugin. In order to do that, run the following commands:

.. code-block:: console

 $ heroku addons:create bonsai:sandbox-6 --version=5.4
 $ heroku run python manage.py search_index --create
