Installation for Linux
======================

.. note::

   If you prefer using containers or have problems with configuring PostgreSQL, Redis and Elasticsearch, try :ref:`docker-dev` instructions.


Prerequisites
-------------

Before you are ready to run Saleor you will need additional software installed on your computer.


Python 3
~~~~~~~~

Saleor requires Python 3.4 or later. A compatible version comes preinstalled with most current Linux systems. If that is not the case consult your distribution for instructions on how to install Python 3.6.


Node.js
~~~~~~~

Version 8 or later is required. See the `installation instructions <https://nodejs.org/en/download/package-manager/>`_.

.. note::

   Debian and Ubuntu users who install Node.js using system packages will also need to install the ``nodejs-legacy`` package.


PostgreSQL
~~~~~~~~~~

Saleor needs PostgreSQL version 9.4 or above to work. Use the `PostgreSQL download page <https://www.postgresql.org/download/>`_ to get instructions for your distribution.


Gtk+
~~~~

Some features like PDF creation require that additional system libraries are present.

Debian / Ubuntu
_______________

Debian 9.0 Stretch or newer, Ubuntu 16.04 Xenial or newer:

.. code-block:: console

 $ sudo apt-get install build-essential python3-dev python3-pip python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

Fedora
______

.. code-block:: console

 $ sudo yum install redhat-rpm-config python-devel python-pip python-cffi libffi-devel cairo pango gdk-pixbuf2

Archlinux
_________

.. code-block:: console

 $ sudo pacman -S python-pip cairo pango gdk-pixbuf2 libffi pkg-config

Gentoo
______

.. code-block:: console

 $ emerge pip cairo pango gdk-pixbuf cffi


Installation
------------

#. Clone the repository (or use your own fork):

   .. code-block:: console

    $ git clone https://github.com/mirumee/saleor.git


#. Enter the directory:

   .. code-block:: console

    $ cd saleor/


#. Install all dependencies:

   We strongly recommend `creating a virtual environment <https://docs.python.org/3/tutorial/venv.html>`_ before installing any Python packages.

   .. code-block:: console

    $ pip install -r requirements.txt


#. Set ``SECRET_KEY`` environment variable.

   We try to provide usable default values for all of the settings.
   We've decided not to provide a default for ``SECRET_KEY`` as we fear someone would inevitably ship a project with the default value left in code.

   .. code-block:: console

    $ export SECRET_KEY='<mysecretkey>'

   .. warning::

       Secret key should be a unique string only your team knows.
       Running code with a known ``SECRET_KEY`` defeats many of Django’s security protections, and can lead to privilege escalation and remote code execution vulnerabilities.
       Consult `Django's documentation <https://docs.djangoproject.com/en/1.11/ref/settings/#secret-key>`_ for details.


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

   .. code-block:: console

    $ python manage.py migrate

   .. warning::

       This command will need to be able to create database extensions. If you get an error related to the ``CREATE EXTENSION`` command please review the notes from the user creation step.

#. Install front-end dependencies:

   .. code-block:: console

    $ npm install

   .. note::

       If this step fails go back and make sure you're using new enough version of Node.js.

#. Prepare front-end assets:

   .. code-block:: console

    $ npm run build-assets

#. Compile e-mails:

   .. code-block:: bash

    $ npm run build-emails

#. Start the development server:

   .. code-block:: console

    $ python manage.py runserver
