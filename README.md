Saleor
======

Avast ye landlubbers! Saleor be a Satchless store ye can fork.

[![Build Status](https://travis-ci.org/mirumee/saleor.png?branch=master)](https://travis-ci.org/mirumee/saleor)


Usage
-----

1. Use `django-admin.py` to start a new project using Saleor as template:

   ```
   $ django-admin.py startproject \
   --template=https://github.com/mirumee/saleor/archive/master.zip myproject
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
4. Prepare the database:

   ```
   $ saleor syncdb --all
   ```

   `saleor` is a shortcut for running `python manage.py` so you can use it to execute all management commands.


Testing changes
---------------

Run the tests to make sure everything works:

```
$ python setup.py test
```
