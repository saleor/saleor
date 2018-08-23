Installation for macOS
======================

Prerequisites
-------------

Before you are ready to run Saleor you will need additional software installed on your computer.


Node.js
~~~~~~~

Version 10 or later is required. Download the macOS installer from the `Node.js downloads page <https://nodejs.org/en/download/>`_.


PostgreSQL
~~~~~~~~~~

Saleor needs PostgreSQL version 9.4 or above to work. Get the macOS installer from the `PostgreSQL download page <https://www.postgresql.org/download/macosx/>`_.

Command Line Tools for Xcode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Download and install the latest version of "Command Line Tools (macOS 10.x) for Xcode 9.x" from the `Downloads for Apple Developers page <https://developer.apple.com/download/more/>`_.

Then run:

.. code-block:: console

 $ xcode-select --install


Homebrew
~~~~~~~~

Run the following command:

.. code-block:: console

 $ /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"


Python 3
~~~~~~~~

Use Homebrew to install the latest version of Python 3:

.. code-block:: console

 $ brew install python3


Git
~~~

Use Homebrew to install Git:

.. code-block:: console

 $ brew install git


Gtk+
~~~~

Use Homebrew to install the graphical libraries necessary for PDF creation:

.. code-block:: console

 $ brew install cairo pango gdk-pixbuf libffi


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

   Unless configured otherwise the store will use ``saleor`` as both username and password. Remember to give your user the ``SUPERUSER`` privilege so it can create databases and database extensions.

   .. code-block:: console

    $ createuser --superuser --pwprompt saleor

   Enter ``saleor`` when prompted for password.

#. Create a PostgreSQL database:

   Unless configured otherwise the store will use ``saleor`` as the database name.

   .. code-block:: console

    $ createdb saleor

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

   .. code-block:: console

    $ npm run build-emails

#. Start the development server:

   .. code-block:: console

    $ python manage.py runserver
