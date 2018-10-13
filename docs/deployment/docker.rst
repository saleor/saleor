.. _docker-deployment:

Docker
======

You will need to install Docker first.

Then use Docker to build the image:

.. code-block:: bash

 $ docker build --build-arg MODE=prod -t mystorefront .
