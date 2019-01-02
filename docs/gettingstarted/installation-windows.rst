Installation for Windows
========================

This guide assumes a 64-bit installation of Windows.


Prerequisites
-------------

Before you are ready to run Saleor you will need additional software installed on your computer.


Python
~~~~~~

Download the latest **3.7** Windows installer from the `Python download page <https://www.python.org/downloads/>`_ and follow the instructions.

Make sure that "**Add Python 3.7 to PATH**" is checked.


Node.js
~~~~~~~

Version 10 or later is required. Download the Windows installer from the `Node.js downloads page <https://nodejs.org/en/download/>`_.

Make sure that "**Add to PATH**" is selected.


PostgreSQL
~~~~~~~~~~

Saleor needs PostgreSQL version 9.4 or above to work. Get the Windows installer from the `project's download page <https://www.postgresql.org/download/windows/>`_.

Make sure you keep track of the password you set for the administration account during installation.


GTK+
~~~~

Download the `64-bit Windows installer <https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer>`_.

Make sure that "**Set up PATH environment variable to include GTK+**" is selected.


Compilers
~~~~~~~~~

Please download and install the latest version of the `Build Tools for Visual Studio <https://go.microsoft.com/fwlink/?linkid=840931>`_.


Installation
------------

All commands need to be performed in either PowerShell or a Command Shell.

#. Clone the repository (replace the URL with your own fork where needed):

   .. code-block:: powershell

    git clone https://github.com/mirumee/saleor.git


#. Enter the directory:

   .. code-block:: powershell

    cd saleor/


#. Install all dependencies:

   We strongly recommend `creating a virtual environment <https://docs.python.org/3/tutorial/venv.html>`_ before installing any Python packages.

   .. code-block:: powershell

    python -m pip install -r requirements.txt


#. Set ``SECRET_KEY`` environment variable.

   We try to provide usable default values for all of the settings.
   We've decided not to provide a default for ``SECRET_KEY`` as we fear someone would inevitably ship a project with the default value left in code.

   .. code-block:: powershell

    $env:SECRET_KEY = "<mysecretkey>"

   .. warning::

       Secret key should be a unique string only your team knows.
       Running code with a known ``SECRET_KEY`` defeats many of Django’s security protections, and can lead to privilege escalation and remote code execution vulnerabilities.
       Consult `Django's documentation <https://docs.djangoproject.com/en/1.11/ref/settings/#secret-key>`_ for details.


#. Create a PostgreSQL user:

   Use the **pgAdmin** tool that came with your PostgreSQL installation to create a database user for your store.

   Unless configured otherwise the store will use ``saleor`` as both username and password. Remember to give your user the ``SUPERUSER`` privilege so it can create databases and database extensions.

#. Create a PostgreSQL database

   See `PostgreSQL's createdb command <https://www.postgresql.org/docs/current/static/app-createdb.html>`_ for details.

   .. note::

       Database name is extracted from the ``DATABASE_URL`` environment variable. If absent it defaults to ``saleor``.

#. Prepare the database:

   .. code-block:: powershell

    python manage.py migrate

   .. warning::

       This command will need to be able to create a database and some database extensions. If you get an error related to these make sure you've properly assigned your user ``SUPERUSER`` privileges.

#. Install front-end dependencies:

   .. code-block:: powershell

    npm install

   .. note::

       If this step fails go back and make sure you're using new enough version of Node.js.

#. Prepare front-end assets:

   .. code-block:: powershell

    npm run build-assets

#. Compile e-mails:

   .. code-block:: powershell

    npm run build-emails

#. Start the development server:

   .. code-block:: powershell

    python manage.py runserver
