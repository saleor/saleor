.. _docker-deployment:

Docker
======

You will need to install Docker first.

Before building the image make sure you have all of the front-end assets prepared for production:

.. code-block:: bash

 $ npm run build-assets --production
 $ python manage.py collectstatic

Then use Docker to build the image:

.. code-block:: bash

 $ docker build -t mystorefront .
