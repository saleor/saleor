Saleor
======

Avast ye landlubbers! Saleor be a Satchless store ye can fork.

[![Build Status](https://travis-ci.org/mirumee/saleor.png?branch=master)](https://travis-ci.org/mirumee/saleor)


Usage
-----

1. Use `django-admin.py` to start a new project using Saleor as template:

   ```
   $ django-admin.py startproject --template=https://github.com/mirumee/saleor/archive/master.zip myproject
   ```
2. Enter the directory:

   ```
   $ cd myproject/
   ```
3. Install it in development mode:

   ```
   $ python setup.py develop
   ```
   (For production use `python setup.py install` instead.)
4. Prepare the database¹:

   ```
   $ saleor syncdb --all
   ```
5. Run `saleor runserver`¹ to start the development server
6. Edit the code to have it suite your requirements
7. Run the tests to make sure everything works:

   ```
   $ python setup.py test
   ```
8. Deploy!

¹ `saleor` is a shortcut for running `python manage.py` so you can use it to execute all management commands.
