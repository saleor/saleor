.. _docker-deployment:

Docker
======

You will need to install Docker first.

Then use Docker to build the image:

.. code-block:: bash

 $ docker build -t mystorefront .


Then you can run saleor container with the minimal settings:

.. code-block:: bash

 $ docker run -e SECRET_KEY=<SECRET_KEY> -e DATABASE_URL=<DATABASE_URL> -p 8000:8000 saleor

For more environment variable settings, please refer to `Configuration <https://docs.getsaleor.com/en/latest/gettingstarted/configuration.html>`_
