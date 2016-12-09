Getting started
===============

Prerequisites
-------------

Before you are ready to run Saleor you will need certain software installed on your computer.

#. `Python <https://www.python.org/>`_ version 3.5.x or 2.7.x

#. `pip <https://pip.pypa.io/en/stable/installing/>`_ if you're using an older release of Python 2.7

#. ``wheel`` Python package if you're using pip older than 8.1.2

#. `Node.js <https://nodejs.org/>`_ version 4 or above

   .. note::

       Debian and Ubuntu users who install Node.js using system packages will also need to install the ``nodejs-legacy`` package.

#. `webpack module bundler <https://webpack.github.io/>`_ installed globally with:

   .. code-block:: bash

    $ npm i webpack -g

#. `PostgreSQL <https://www.postgresql.org/>`_ version 9.4 or above

We also strongly recommend creating a virtual environment before proceeding with installation.


Installation
------------

#. Clone the repository (or use your own fork):

   .. code-block:: bash

    $ git clone https://github.com/mirumee/saleor.git


#. Enter the directory:

   .. code-block:: bash

    $ cd saleor/


#. Install all dependencies:

   .. code-block:: bash

    $ pip install -r requirements.txt


#. Set ``SECRET_KEY`` environment variable.

   .. note::

       Secret key should be a unique string only your team knows.
       It's serious as this key is used to ensure security of your installation.
       Consult `Django's documentation <https://docs.djangoproject.com/en/1.10/ref/settings/#secret-key>`_ for details.

       We try to provide usable default values for all of the settings.
       We've decided not to provide a default for ``SECRET_KEY`` as we fear someone would inevitably ship a project with the default value left in code.

   .. code-block:: bash

    $ export SECRET_KEY='<mysecretkey>'


#. Prepare the database:

   .. code-block:: bash

    $ python manage.py migrate


#. Install front-end dependencies:

   .. code-block:: bash

    $ npm install

   .. note::

       If this step fails go back and make sure you're using new enough versions of Node.js and npm.

#. Prepare front-end assets:

   .. code-block:: bash

    $ npm run build-assets


#. Run like a normal django project:

   .. code-block:: bash

    $ python manage.py runserver


Example data
------------

If you'd like some data to test your new storefront you can populate the database with example products and orders:

.. code-block:: bash

 $ python manage.py populatedb
