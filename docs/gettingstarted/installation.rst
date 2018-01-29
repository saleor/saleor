Installation
============

.. note::

   If you prefer using containers or have problems with configuring PostgreSQL, Redis and Elasticsearch, try :ref:`docker_dev` instructions.


Prerequisites
-------------

Before you are ready to run Saleor you will need certain software installed on your computer.


Python 3
~~~~~~~~

Saleor requires Python 3.4 or later. To install the latest version visit the `Python download page <https://www.python.org/downloads/>`_ and follow the instructions.

   .. note::

       Saleor does work with PyPy 3.5 but you'll need to replace the default PostgreSQL driver with a ``cffi``-based one.


Node.js
~~~~~~~

Version 8 or later is required.

**Windows** users can `download an official Node.js installer <https://nodejs.org/en/download/>`_.

**macOS** and **Linux** users can `install Node.js using a package manager <https://nodejs.org/en/download/package-manager/>`_.

   .. note::

       Debian and Ubuntu users who install Node.js using system packages will also need to install the ``nodejs-legacy`` package.


PostgreSQL
~~~~~~~~~~

Saleor needs PostgreSQL version 9.4 or above to work. Please visit `the project's download page <https://www.postgresql.org/download/>`_ for details.


System dependencies
~~~~~~~~~~~~~~~~~~~

Some features like PDF creation require that additional system libraries are present.

**Windows** users should follow the `WeasyPrint instructions for Windows <http://weasyprint.readthedocs.io/en/latest/install.html#windows>`_.

**macOS** users should follow the `WeasyPrint instructions for OS X <http://weasyprint.readthedocs.io/en/latest/install.html#os-x>`_.

**Linux** users should follow the `WeasyPrint instructions for Linux <http://weasyprint.readthedocs.io/en/latest/install.html#linux>`_.


Installation
------------

#. Clone the repository (or use your own fork):

   .. code-block:: bash

    $ git clone https://github.com/mirumee/saleor.git


#. Enter the directory:

   .. code-block:: bash

    $ cd saleor/


#. Install all dependencies:

   We strongly recommend `creating a virtual environment <https://docs.python.org/3/tutorial/venv.html>`_ before installing any Python packages.

   .. code-block:: bash

    $ pip install -r requirements.txt


#. Set ``SECRET_KEY`` environment variable.

   .. note::

       Secret key should be a unique string only your team knows.
       Running code with a known ``SECRET_KEY`` defeats many of Django’s security protections, and can lead to privilege escalation and remote code execution vulnerabilities.
       Consult `Django's documentation <https://docs.djangoproject.com/en/1.11/ref/settings/#secret-key>`_ for details.

       We try to provide usable default values for all of the settings.
       We've decided not to provide a default for ``SECRET_KEY`` as we fear someone would inevitably ship a project with the default value left in code.

   .. code-block:: bash

    $ export SECRET_KEY='<mysecretkey>'


#. Create a PostgreSQL user:

   See `PostgreSQL's createuser command <https://www.postgresql.org/docs/current/static/app-createuser.html>`_ for details.

   .. note::

       You need to create the user to use within your project.
       Username and password are extracted from the ``DATABASE_URL`` environmental variable. If absent they both default to ``saleor``.

   .. warning::

       While creating the database Django will need to create some PostgreSQL extensions if not already present in the database. This requires a superuser privilege.

       For local development you can grant your database user the ``SUPERUSER`` privilege. For publicly available systems we recommend using a separate privileged user to perform database migrations.


#. Create a PostgreSQL database

   See `PostgreSQL's createdb command <https://www.postgresql.org/docs/current/static/app-createdb.html>`_ for details.

   .. note::

       Database name is extracted from the ``DATABASE_URL`` environmental variable. If absent it defaults to ``saleor``.


#. Prepare the database:

   .. code-block:: bash

    $ python manage.py migrate

   .. warning::

       This command will need to be able to create database extensions. If you get an error related to the ``CREATE EXTENSION`` command please review the notes from the user creation step.

#. Install front-end dependencies:

   .. code-block:: bash

    $ npm install

   .. note::

       If this step fails go back and make sure you're using new enough version of Node.js.

#. Prepare front-end assets:

   .. code-block:: bash

    $ npm run build-assets


#. Start the development server:

   .. code-block:: bash

    $ python manage.py runserver


Example data
------------

If you'd like some data to test your new storefront you can populate the database with example products and orders:

.. code-block:: bash

 $ python manage.py populatedb
