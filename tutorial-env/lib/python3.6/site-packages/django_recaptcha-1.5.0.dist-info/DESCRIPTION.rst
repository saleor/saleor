Django reCAPTCHA
================
**Django reCAPTCHA form field/widget integration app.**

.. image:: https://travis-ci.org/praekelt/django-recaptcha.svg?branch=develop
    :target: https://travis-ci.org/praekelt/django-recaptcha
.. image:: https://coveralls.io/repos/github/praekelt/django-recaptcha/badge.svg?branch=develop
    :target: https://coveralls.io/github/praekelt/django-recaptcha?branch=develop
.. image:: https://badge.fury.io/py/django-recaptcha.svg
    :target: https://badge.fury.io/py/django-recaptcha

.. contents:: Contents
    :depth: 5

Django reCAPTCHA uses a modified version of the `Python reCAPTCHA client
<http://pypi.python.org/pypi/recaptcha-client>`_ which is included in the
package as ``client.py``.

NOTE:
-----

As of March 2018 the reCAPTCHA v1 Google endpoints no longer exist.
Currently django-recaptcha still makes use of those endpoints when either
``CAPTCHA_AJAX = True`` or ``NOCAPTCHA = False``. To make use of the default reCAPTCHA v2
checkbox, please ensure ``NOCAPTCHA = True`` and ``CAPTCHA_AJAX`` is not present in
your project settings.
Moving forward, this project will be removing the lingering reCAPTCHA v1 and
the need to add ``NOCAPTCHA = True`` for reCAPTCHA v2 support.

Requirements
------------

Tested with:

* Python: 2.7, 3.5, 3.6, 3.7
* Django: 1.11, 2.0, 2.1

Installation
------------

#. `Sign up for reCAPTCHA <https://www.google.com/recaptcha/intro/index.html>`_.

#. Install with ``pip install django-recaptcha``.

#. Add ``'captcha'`` to your ``INSTALLED_APPS`` setting.

#. Add the keys reCAPTCHA have given you to your Django production settings (leave development settings blank to use the default test keys) as
   ``RECAPTCHA_PUBLIC_KEY`` and ``RECAPTCHA_PRIVATE_KEY``. For example:

   .. code-block:: python

       RECAPTCHA_PUBLIC_KEY = 'MyRecaptchaKey123'
       RECAPTCHA_PRIVATE_KEY = 'MyRecaptchaPrivateKey456'

   These can also be specificied per field by passing the ``public_key`` or
   ``private_key`` parameters to ``ReCaptchaField`` - see field usage below.

#. To ensure the reCAPTCHA V2 endpoints are used add the setting:

   .. code-block:: python

       NOCAPTCHA = True # Marked for deprecation

#. To make use of the invisible reCAPTCHA V2, ensure ``NOCAPTCHA = True`` is present in your settings and then also dd:

   .. code-block:: python

       RECAPTCHA_V2_INVISIBLE = True # Marked for deprecation

Out of the box the invisible implementation only supports one form with the reCAPTCHA widget on a page. This widget must be wrapped in a form element.
To alter the JavaScript behaviour to suit your project needs, override ``captcha/includes/js_v2_invisible.html`` in your local project template directory.

#. If you require a proxy, add a ``RECAPTCHA_PROXY`` setting, for example:

   .. code-block:: python

       RECAPTCHA_PROXY = 'http://127.0.0.1:8000'

Usage
-----

Field
~~~~~

The quickest way to add reCAPTCHA to a form is to use the included
``ReCaptchaField`` field class. A ``ReCaptcha`` widget will be rendered with
the field validating itself without any further action required. For example:

.. code-block:: python

    from django import forms
    from captcha.fields import ReCaptchaField

    class FormWithCaptcha(forms.Form):
        captcha = ReCaptchaField()

To allow for runtime specification of keys you can optionally pass the
``private_key`` or ``public_key`` parameters to the constructor. For example:

.. code-block:: python

    captcha = ReCaptchaField(
        public_key='76wtgdfsjhsydt7r5FFGFhgsdfytd656sad75fgh',
        private_key='98dfg6df7g56df6gdfgdfg65JHJH656565GFGFGs',
    )

If specified these parameters will be used instead of your reCAPTCHA project
settings.

The reCAPTCHA widget supports several `Javascript options variables
<https://developers.google.com/recaptcha/docs/display#js_param>`_ that
customize the behaviour of the widget, such as ``theme`` and ``lang``. You can
forward these options to the widget by passing an ``attr`` parameter to the
field, containing a dictionary of options. For example:

.. code-block:: python

    captcha = ReCaptchaField(attrs={
      'theme' : 'clean',
    })

The client takes the key/value pairs and writes out the ``RecaptchaOptions``
value in JavaScript.


Local Development and Functional Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Google provides test keys which are set as the default for ``RECAPTCHA_PUBLIC_KEY`` and ``RECAPTCHA_PRIVATE_KEY``. These cannot be used in production since they always validate to true and a warning will be shown on the reCAPTCHA.


AJAX(Marked for deprecation)
~~~~~

To make reCAPTCHA work in ajax-loaded forms:

#. Import ``recaptcha_ajax.js`` on your page (not in the loaded template):

   .. code-block:: html

       <script type="text/javascript" src="http://www.google.com/recaptcha/api/js/recaptcha_ajax.js"></script>

#. Add to your Django settings:

   .. code-block:: python

       CAPTCHA_AJAX = True


Disabling SSL
~~~~~~~~~~~~~

This library used to not use SSL by default, but now it does. You can disable
this if required, but you should think long and hard about it before you do so!

You can disable it by setting ``RECAPTCHA_USE_SSL = False`` in your Django
settings, or by passing ``use_ssl=False`` to the constructor of
``ReCaptchaField``.


Credits
-------
Inspired Marco Fucci's blogpost titled `Integrating reCAPTCHA with Django
<http://www.marcofucci.com/tumblelog/26/jul/2009/integrating-recaptcha-with-django>`_


``client.py`` taken from `recaptcha-client
<http://pypi.python.org/pypi/recaptcha-client>`_ licenced MIT/X11 by Mike
Crawford.

reCAPTCHA copyright 2012 Google.


Authors
=======

Praekelt Consulting
-------------------
* Shaun Sephton
* Peter Pistorius
* Hedley Roos
* Altus Barry
* Cilliers Blignaut

bTaylor Design
--------------
* `Brandon Taylor <http://btaylordesign.com/>`_

Other
-----
* Brooks Travis
* `Denis Mishchishin <https://github.com/denz>`_
* `Joshua Peper <https://github.com/zout>`_
* `Rodrigo Primo <https://github.com/rodrigoprimo>`_
* `snnwolf <https://github.com/snnwolf>`_
* `Adriano Orioli <https://github.com/Aorioli>`_
* `cdvv7788 <https://github.com/cdvv7788>`_
* `Daniel Gatis Carrazzoni <https://github.com/danielgatis>`_
* `pbf <https://github.com/pbf>`_
* `Alexey Subbotin <https://github.com/dotsbb>`_
* `Sean Stewart <https://github.com/mindcruzer>`_


Changelog
=========

1.5.0 (2019-01-09)
------------------

#. Added testing for Django 2.1 (no code changes needed).
#. Update the unit tests to no longer make use of reCAPTCHA v1.
#. Added deprecation warnings for reCAPTCHA v1 support.
#. Remove the need for RECAPTCHA_TESTING environment variable during unit testing.
#. Added Invisible reCAPTCHA V2 support.

1.4.0 (2018-02-08)
------------------

#. Dropped support for Django < 1.11.
#. Added testing for Django 2.0 (no code changes needed).

1.3.1 (2017-06-27)
------------------

#. Fixed widget attributes regression for Django < 1.10.

1.3.0 (2017-04-10)
------------------

#. Support Django 1.11 in addition to 1.8, 1.9, and 1.10.


1.2.1 (2017-01-23)
------------------

#. Made reCAPTCHA test keys the default keys for easy use in development. The
   captcha doesn't require any interaction, has a warning label that it's for
   testing purposes only, and always validates.

1.2.0 (2016-12-19)
------------------

#. Pass options as HTML data attributes instead of the ``RecaptchaOptions``
   JavaScript object in the default template. Custom templates using
   ``RecaptchaOptions`` should migrate to using HTML data attributes.

1.1.0 (2016-10-28)
------------------

#. Dropped support for old Django versions. Only the upstream supported
   versions are now supported, currently 1.8, 1.9, and 1.10.
#. Made recaptcha checking use SSL by default. This can be disabled by setting
   ``RECAPTCHA_USE_SSL = False`` in your Django settings or passing
   ``use_ssl=False`` to the constructor of ``ReCaptchaField``.
#. Made ReCaptchaField respect required=False

1.0.6 (2016-10-05)
------------------

#. Confirmed tests pass on Django 1.10. Older versions should still work.
#. Fixed a bug where the widget was always rendered in the first used language
   due to ``attrs`` being a mutable default argument.

1.0.5 (2016-01-04)
------------------
#. Chinese translation (kz26).
#. Syntax fix (zvin).
#. Get tests to pass on Django 1.9.

1.0.4 (2015-04-16)
------------------
#. Fixed Python 3 support
#. Added Polish translations
#. Update docs

1.0.3 (2015-01-13)
------------------
#. Added nocaptcha recaptcha support

1.0.2 (2014-09-16)
------------------
#. Fixed Russian translations
#. Added Spanish translations

1.0.1 (2014-09-11)
------------------
#. Added Django 1.7 suport
#. Added Russian translations
#. Added multi dependancy support
#. Cleanup

1.0 (2014-04-23)
----------------
#. Added Python 3 support
#. Added French, Dutch and Brazilian Portuguese translations

0.0.9 (2014-02-14)
------------------
#. Bugfix: release master and not develop. This should fix the confusion due to master having been the default branch on Github.

0.0.8 (2014-02-13)
------------------
#. Bugfix: remove reference to options.html.

0.0.7 (2014-02-12)
------------------
#. Make it possible to load the widget via ajax.

0.0.6 (2013-01-31)
------------------
#. Added an extra parameter `lang` to bypass Google's language bug. See http://code.google.com/p/recaptcha/issues/detail?id=133#c3
#. widget.html no longer includes options.html. Options are added directly to widget.html

0.0.5 (2013-01-17)
------------------
#. Removed django-registration dependency
#. Changed testing mechanism to environmental variable `RECAPTCHA_TESTING`

0.0.4
-----
#. Handle missing REMOTE_ADDR request meta key. Thanks Joe Jasinski.
#. Added checks for settings.DEBUG to facilitate tests. Thanks Victor Neo.
#. Fix for correct iframe URL in case of no javascript. Thanks gerdemb.

0.0.3 (2011-09-20)
------------------
#. Don't force registration version thanks kshileev.
#. Render widget using template, thanks denz.

0.0.2 (2011-08-10)
------------------
#. Use remote IP when validating.
#. Added SSL support, thanks Brooks Travis.
#. Added support for Javascript reCAPTCHA widget options, thanks Brandon Taylor.
#. Allow for key and ssl specification at runtime, thanks Evgeny Fadeev.

0.0.1 (2010-06-17)
------------------
#. Initial release.


