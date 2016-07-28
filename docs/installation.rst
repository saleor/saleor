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

   .. code:: bash

       $ npm i webpack -g

We also strongly recommend creating a virtual environment before proceeding with installation.


Installation
------------

#. Clone the repository (or use your fork):

   .. code:: bash

       $ git clone https://github.com/mirumee/saleor.git


#. Enter the directory:

   .. code:: bash

       $ cd saleor/


#. Install all dependencies:

   .. code:: bash

       $ pip install -r requirements.txt


#. Set `SECRET_KEY` environmental variable.

   .. note::

       Secret key has to be unique and must not be shared with anybody.

   .. code:: bash

       $ export SECRET_KEY='mysecretkey'


#. Prepare the database:

   .. code:: bash

       $ python manage.py migrate


#. Install front-end dependencies:

   .. code:: bash

       $ npm install


#. Prepare front-end assets:

   .. code:: bash

    $ npm run build-assets


#. Run like a normal django project:

   .. code:: bash

    $ python manage.py runserver
