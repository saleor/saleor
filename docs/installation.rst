Getting started
===============

Prerequisites
-------------

Before you are ready to run Saleor you will need certain software installed on your computer.

#. `Python <https://www.python.org/>`_ version 3.5 or 2.7

#. `pip <https://pip.pypa.io/en/stable/installing/>`_ if you're using an older release of Python 2.7

#. `Node.js <https://nodejs.org/>`_ version 4 or above

   .. note::

       Debian and Ubuntu users who install Node.js using system packages will also need to install the ``nodejs-legacy`` package.

#. `webpack module bundler <https://webpack.github.io/>`_ installed globally with:

   .. code-block:: bash

    $ npm i webpack -g

We also strongly recommend creating a virtual environment before proceeding with installation.


Installation
------------

#. Clone the repository (or use your fork):

   .. code-block:: bash

    $ git clone https://github.com/mirumee/saleor.git


#. Enter the directory:

   .. code-block:: bash

    $ cd saleor/


#. Install all dependencies:

   .. code-block:: bash

    $ pip install -r requirements.txt


#. Set `SECRET_KEY` environmental variable.

   .. note::

       Secret key has to be unique and must not be shared with anybody.

   .. code-block:: bash

    $ export SECRET_KEY='mysecretkey'


#. Prepare the database:

   .. code-block:: bash

    $ python manage.py migrate


#. Install front-end dependencies:

   .. code-block:: bash

    $ npm install


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
