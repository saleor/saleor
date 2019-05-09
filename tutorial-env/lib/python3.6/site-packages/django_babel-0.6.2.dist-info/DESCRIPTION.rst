Tools for using Babel with Django
=================================

This package contains various utilities for integration of `Babel`_ into the
`Django`_ web framework:

 * A message extraction plugin for Django templates.
 * A middleware class that adds the Babel `Locale`_ object to requests.
 * A set of template tags for date and number formatting.


Extracting Messages
-------------------

Babel provides a message extraction framework similar to GNU ``xgettext``, but
more extensible and geared towards Python applications. While Django does
provide `wrapper scripts`_ for making the use of ``xgettext`` more
convenient, the extraction functionality is rather limited. For example, you
can't use template files with an extension other than ``.html``, and everything
needs to be in your project package directory.

Extraction Method Mapping
^^^^^^^^^^^^^^^^^^^^^^^^^

So django-babel comes with an extraction method plugin that can extract
localizable messages from Django template files. Python is supported out of the
box by Babel. To use this extraction functionality, create a file called
``babel.cfg`` in your project directory (the directory above your project
package), with the content:

.. code-block:: ini

    [django: templates/**.*]
    [django: mypkg/*/templates/**.*]
    [python: mypkg/**.py]

This instructs Babel to look for any files in the top-level ``templates``
directory, or any files in application ``templates`` directories, and use the
extraction method named “django” to extract messages from those template files.
You'll need to adjust those glob patterns to wherever you my be storing your
templates.

Also, any files with the extension ``.py`` inside your package directory (replace
“mypkg” with the actual name of your Django project package) are processed by
the “python” extraction method.

If you don't use setuptools, or for some reason haven't installed django-babel
using setuptools/pip, you'll need to define what function the extraction method
“django” maps to. This is done in an extra section at the top of the
configuration file:

.. code-block:: ini

    [extractors]
    django = django_babel.extract:extract_django

The encoding of the templates is assumed to be UTF-8. If you are using a
different encoding, you will need to specify it in the configuration. For
example:

.. code-block:: ini

    [django: templates/**.*]
    encoding = iso-8859-1


Running the Extraction Process
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once you've set up the configuration file, the actual extraction is performed
by executing the command-line program ``pybabel`` which is installed alongside
the Babel package:

.. code-block:: bash

    $ cd projectdir
    $ pybabel extract -F babel.cfg -o mypkg/locale/django.pot .

This creates the PO file template in ``mypkg/locale/django.pot``.


Creating and Updating Translations Catalogs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you don't already have translation catalogs, you need to create them. This
is done using the ``pybabel init`` command:

.. code-block:: bash

    $ pybabel init -D django -i mypkg/locale/django.pot -d mypkg/locale -l en_US
    $ pybabel init -D django -i mypkg/locale/django.pot -d mypkg/locale -l de_DE

This should create two files: ``mypkg/locale/en_US/django.po`` and
``mypkg/locale/de_DE/django.po``. These files are where you put the actual
translations.

When you modify your Python source files or your templates, you genereally need
to sync the translation catalogs. For that, you first perform a fresh
extraction as described in the previous section, so that the ``django.pot`` file
gets updated.

Then, you run the ``pybabel update`` command to merge the changes into the
translation catalogs:

```bash
$ pybabel update -D django -i mypkg/locale/django.pot -d mypkg/locale
```

This will update all the ``.po`` files found in the ``mypkg/locale`` directory.


Compiling Translations Catalogs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Finally, you need to compile those ``.po`` files to binary ``.mo`` files. Use the
`pybabel compile` command for that:

.. code-block:: bash

    $ pybabel compile -D django -d mypkg/locale

Add the ``--statistics`` option to get information about the completeness of your
translations:

.. code-block:: bash

    $ pybabel compile -D django -d mypkg/locale --statistics


Using ``setup.py``
^^^^^^^^^^^^^^^^^^

Much of the above process can be automated if you add a ``setup.py`` script to
your project and use the distutils/setuptools commands that come with Babel.
This is described at `Distutils/Setuptools Integration`_.


Using the Middleware
--------------------

To use the Babel middleware, add it to the list of ``MIDDLEWARE_CLASSES`` in your
settings module. If you're also using Django's own ``LocaleMiddleware`` to vary
the locale based on user preference, the Babel middleware must be inserted
after the Django one:

.. code-block:: python

    MIDDLEWARE_CLASSES = (
        ...
        'django.middleware.locale.LocaleMiddleware',
        'django_babel.middleware.LocaleMiddleware',
        ...
    )

This adds a ``locale`` attribute to the request object, which is an instance of
the Babel ``Locale`` class. You can access the locale via ``request.locale`` when
the request object is available, or otherwise use the
``django_babel.middleware.get_current_locale()`` function to get the current
locale from a thread-local cache.


Using the Template Tags
-----------------------

The template filters provided by django-babel allow formatting of date/time and
number values in a locale-sensitive manner, providing much more powerful
alternatives to the ``date``, ``time``, and ``floatformat`` filters that come with
Django.

To make the template filters/tags available, you need to add django-babel to
the list of ``INSTALLED_APPS`` in your settings module:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'django_babel',
        ...
    )

And in every template you want to use the filters, you need to explicitly load
the django-babel library:

.. code-block:: django

    {% load babel %}

General information on date/time and number formatting can be found at
`Date Formatting`_ and `Number Formatting`_.

The following filters are made available. The examples assume a locale of
``en_US``.


``datefmt``
^^^^^^^^^^^

Renders a string representation of a date.

* **Input**:  ``datetime.date``, ``datetime.datetime``, or a float/int timestamp
* **Parameters**:  the format name or pattern (optional)

Assuming that ``book.pubdate`` returns a ``datetime.date`` or
``datetime.datetime`` object:

.. code-block:: django

    {{ book.pubdate|datefmt:"short" }}

would render: **4/1/07**, and

.. code-block:: django

    {{ book.pubdate|datefmt:"E, MMM dd yyyy GGG" }}

would render: **Sun, Apr 01 2007 AD**

``datetimefmt``
^^^^^^^^^^^^^^^

Renders a string representation of a date and time.

* **Input**:  ``datetime.datetime``, or a float/int timestamp
* **Parameters**:  the format name or pattern (optional)

Examples:

.. code-block:: django

    {{ book.pubdate|datetimefmt:"short" }}

would render: **4/1/07 3:30 PM**, and

.. code-block:: django

    {{ book.pubdate|datetimefmt:"E, MMM dd yyyy GGG' - 'HH:mm:ss'" }}

would render: **Sun, Apr 01 2007 AD - 15:30:00**

``timefmt``
^^^^^^^^^^^

Renders a string representation of a time.

* **Input**:  ``datetime.datetime``, ``datetime.time``, or a float/int timestamp
* **Parameters**:  the format name or pattern (optional)

Examples:

.. code-block:: django

    {{ book.pubdate|timefmt:"short" }}

would render: **3:30 PM**, and

.. code-block:: django

    {{ book.pubdate|timefmt:"h 'o''clock' a'" }}

would render: **3 o'clock PM**

``decimalfmt``
^^^^^^^^^^^^^^

Renders a string representation of a decimal number.

* **Input**:  a `Decimal` object, or a float/int/long value
* **Parameters**:  the format name or pattern (optional)

Examples:

.. code-block:: django

    {{ book.pagecount|decimalfmt }}

would render: **1,234**, and

.. code-block:: django

    {{ book.pagecount|decimalfmt:"#,##0.00" }}

would render: **1,234.00**

``currencyfmt``
^^^^^^^^^^^^^^^

Renders a number formatted as a currency value.

* **Input**:  a ``Decimal`` object, or a float/int/long value
* **Parameters**:  the currency code

Examples:

.. code-block:: django

    {{ book.price|currencyfmt:"USD" }}

would render: **$49.90**

``percentfmt``
^^^^^^^^^^^^^^

Renders a string representation of a number as a percentage.

* **Input**:  a ``Decimal`` object, or a float/int/long value
* **Parameters**:  the format name or pattern (optional)

Examples:

Assuming ``book.rebate`` would return ``0.15``,

.. code-block:: django

    {{ book.rebate|percentfmt }}

would render **15%**, and

.. code-block:: django

    {{ book.rebate|percentfmt:"#,##0.00%" }}

would render **15.00%**.

``scientificfmt``
^^^^^^^^^^^^^^^^^

Renders a string representation of a number using scientific notation.

* **Input**:  a ``Decimal`` object, or a float/int/long value
* **Parameters**:  none

Examples:

Assuming ``book.numsold`` would return 1.000.000,

.. code-block:: django

    {{ book.numsold|scientificfmt }}

would render **10E5**.



.. _Babel: http://babel.pocoo.org/
.. _Django: https://www.djangoproject.com/
.. _wrapper scripts: https://docs.djangoproject.com/en/dev/topics/i18n/translation/#localization-how-to-create-language-files
.. _Distutils/Setuptools Integration: http://babel.pocoo.org/en/stable/setup.html
.. _Date Formatting: http://babel.pocoo.org/en/stable/dates.html
.. _Number Formatting: http://babel.pocoo.org/en/stable/numbers.html
.. _Locale: http://babel.pocoo.org/en/stable/api/core.html#babel.core.Locale


Changelog
=========

0.6.2 (2017-12-18)
------------------

- compatibility with Django 2.0 added


0.6.1 (2017-12-18)
------------------

* compatibility with Django 1.11 added

0.6.0 - 2017-04-25
------------------

* compatibility with unsupported Django versions (<1.8) is dropped
* compatibility with Django 1.10+ middlewares was added

0.5.1 - 2016-03-30
------------------

* make imports absolute in babel templatetags
* strip quotes from translations via _()
* fix links in docs
* Add support for "trimmed" blocktrans content

0.5.0 - 2016-02-29
------------------

* Add compatibility for Django-1.9

0.4.0 - 2015-04-22
------------------

* Add compatibility for Django 1.8
* Add compatibility for latest django master
* Various python 3 fixes


0.3.9 - 2014-12-24
------------------

* Fix dependencies on Django/Babel to use lower-case egg names.

0.3.8 - 2014-10-14
------------------

* Fix old reference to `babeldjango` module in entry points.

0.3.7 - 2014-10-14
------------------

* Fix Python 3.x compatibility in `babel makemessages` command.

0.3.6 - 2014-10-05
------------------

* Django 1.7 compatibility


0.3.5 - 2014-09-10
------------------

* Create .po and .pot files if not existing, plus it's specific base directories.


0.3.4 - 2014-05-25
------------------

* Fixed django compatibility

0.3.3 - 2014-04-22
------------------

* Fixed release builds


0.3.2 - 2014-04-22
------------------

* Initial testing infrastructure
* Add management command `babel` with `makemessages` and `compilemessages`
  labels. Mimics django's `makemessages` and `compilemessages` commands.
* Various unicode fixes


0.3.1 - 2013-12-11
------------------

* fix relative import in template tags


0.3.0 - 2013-12-11
------------------

* Rename package to django_babel


0.2.3 - 2013-12-11
------------------

* Rename package on PyPI
* Use GitHub as source control


.. _`master`: https://github.com/python-babel/django-babel


