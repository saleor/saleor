Installation
============

1. Clone the repository (or use your fork):

   .. code:: bash

    $ git clone https://github.com/mirumee/saleor.git


2. Enter the directory:

   .. code:: bash

    $ cd saleor/


3. Install all dependencies:

   .. code:: bash

    $ pip install -r requirements.txt


4. Set `SECRET_KEY` environmental variable.

   .. note::
    Secret key has to be unique and must not be shared with anybody.

   .. code:: bash

    $ export SECRET_KEY='mysecretkey'


5. Prepare the database:

   .. code:: bash

    $ python manage.py migrate


6. Install front-end dependencies:

   .. note::
    This step requires that you have Node.js installed. On Debian and Ubuntu systems you will also need to install the `nodejs-legacy` package.

   .. code:: bash

    $ npm install


7. Prepare front-end assets:

   .. code:: bash

    $ npm run build-assets


8. Run like a normal django project:

   .. code:: bash

    $ python manage.py runserver


Tests
-----

To run the test suite use:

.. code:: bash

 $ py.test
