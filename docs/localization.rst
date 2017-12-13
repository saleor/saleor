Internationalization
====================

By default language and locale are determined based on the list of preferences supplied by a web browser. GeoIP is used to determine the visitor's country and their local currency.

.. note::

    Saleor uses Transifex to coordinate translations. If you wish to help please head to the `translation dashboard <https://www.transifex.com/mirumee/saleor-1/>`_.

    All translations are handled by the community. All translation teams are open and everyone is welcome to request a new language.

Translation
-----------

Saleor uses ``gettext`` for translation. This is an industry standard for translating software and is the most common way to translate Django applications.

Saleor's storefront and dashboard are both prepared for translation. They use separate translation domains and can be translated separately. All translations provide accurate context descriptions to make translation an easier task.

It is not currently possible to translate database content (like product descriptions) but it's planned for a future release.

Localization
------------

Data formats
************

Saleor uses `Babel <http://babel.pocoo.org/en/latest/>`_ as the interface to Unicode's CLDR library to provide accurate number and date formatting as well as proper currency designation.

Address forms
*************

`Google's address format database <https://github.com/mirumee/google-i18n-address>`_ is used to provide locale-specific address formats and forms. It also takes care of address validation so you don't have to know how to address a package to China or whether United Arab Emirates use postal codes (they don't).

Currency conversion
*******************

Saleor can use currency exchange rate data to show price estimations in the visitor's local currency. Please consult :ref:`openexchangerates` for how to set this up for `Open Exchange Rates <https://openexchangerates.org/>`_.

Phone numbers format
********************

Saleor uses `Google's libphonenumber library <https://github.com/googlei18n/libphonenumber>`_ to ensure provided numbers are correct. You need to choose prefix and type the number separately. No matter what country has been chosen, you may enter phone number belonging to any other country format.
