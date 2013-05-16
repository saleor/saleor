Saleor
======

Avast ye landlubbers! Saleor be a Satchless store ye can fork.

[![Build Status](https://travis-ci.org/mirumee/saleor.png?branch=master)](https://travis-ci.org/mirumee/saleor)


Usage
-----

1. Fork the repo on GitHub (you can skip this step if you like)
1. `git clone` your repository
1. Install it in development mode:

   ```
   $ python setup.py develop
   ```
   (For production use `python setup.py install` instead.)
1. Add a `SECRET_KEY` to your `settings.py` (we did not want to include one out of fear that you'd forget to change it)
1. Prepare the database:

   ```
   $ saleor syncdb --all
   ```
1. Run `saleor runserver`¹ to start the development server (on [localhost:8000](http://localhost:8000/))
1. Edit the code to have it suite your requirements
1. Run the tests to make sure everything works:

   ```
   $ python setup.py test
   ```
1. Deploy!

¹ `saleor` is a shortcut for running `python manage.py` so you can use it to execute all management commands.

