.. _protected-pages-customization:

Protected Pages
===============

Saleor has a mechanism of protected pages, which consists of a list of flagged slugs.
Those protected pages are there to ensure that Saleor parts depending of some pages
are not being accidentally deleted.

Thus, Saleor makes them more difficult to delete them
to make sure the users know what they are doing
and are potentially breaking some Saleor' parts. Which would generate 404 errors.


.. note::

  You can see the list of default existing protected pages in the
  :ref:`pages-architecture` section.


Customizing Protected Slugs
---------------------------

Those slugs are being kept in ``settings.py`` under the key ``PROTECTED_PAGES``.

By default, ``PROTECTED_PAGES`` contains the following data:

.. code-block:: python

  PROTECTED_PAGES = [
      INTERNAL_PAGES['PrivacyPolicy'],
      INTERNAL_PAGES['SellingContract']]


Where:

- ``INTERNAL_PAGES['PrivacyPolicy']`` contains the privacy page's slug (``privacy-policy`` by default);
- ``INTERNAL_PAGES['SellingContract']`` contains the selling contract page's slug (``selling-contract`` by default).


If you want to protect, let's say, a page that you created with the slug ``about-us``,
you would want to append ``about-us`` like that:

.. code-block:: python

  PROTECTED_PAGES = [
      'about-us',
      INTERNAL_PAGES['PrivacyPolicy'],
      INTERNAL_PAGES['SellingContract']]


Or if you wanted to drop the privacy page protection:

.. code-block:: python

  PROTECTED_PAGES = [
      'about-us',
      INTERNAL_PAGES['SellingContract']]
