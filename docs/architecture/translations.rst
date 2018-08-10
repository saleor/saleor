.. _model-translations:

Model Translations
==================

.. note::

    At this stage, model translations are only accessible from the Python code.
    The backend and the storefront are prepared to handle the translated properties, but
    GraphQL API and UI views will be added in the future releases.

Overview
--------

Model translations are available via ``TranslationProxy`` defined on the to-be-translated ``Model``.

``TranslationProxy`` gets user's language, and checks if there's a ``ModelTranslation`` created for that language.

If there's no relevant ``ModelTranslation`` available, it will return the original (therefore not translated) property.
Otherwise, it will return the translated property.

Adding a ModelTranslation
-------------------------

Consider a product.

.. code-block:: python

   from django.db import models

   from saleor.core.utils.translations import TranslationProxy


   class Product(models.Model):
       name = models.CharField(max_length=128)
       description = models.CharField(max_length=256)
       ...

       translated = TranslationProxy()


The product has several properties, but we want to translate just its ``name`` and ``description``.

We've also set a ``translated`` property to an instance of ``TranslationProxy``.

We will use ``ProductTranslation``  to store our translated properties, it requires two base fields:

- ``language_code``
    A language code that this translation correlates to.

- ``product``
    ``ForeignKey`` relation to the translated object (in this case we named it *product*)

... and any other field you'd like to translate, in our example, we will use ``name`` and ``description``.

.. warning:: ``TranslationProxy`` expects that the ``related_name``, on the ``ForeignKey`` relation is set to ``translations``

.. code-block:: python

   from django.db import models


   class ProductTranslation(models.Model):
       language_code = models.CharField(max_length=10)
       product = models.ForeignKey(
           Product, related_name='translations', on_delete=models.CASCADE)
       name = models.CharField(max_length=128)
       description = models.CharField(max_length=256)

       class Meta:
           unique_together = ('product', 'language_code')

.. note:: Don't forget to set ``unique_together`` on the ``product`` and ``language_code``, there should be only one translation per product per language.

.. warning:: ``ModelTranslation`` fields must always take the same arguments as the existing translatable model, eg. inconsistency in ``max_length`` attribute could lead to UI bugs with translation turned on.

Using a ModelTranslation
------------------------

Given the example above, we can access translated properties via the ``TranslationProxy``.

.. code-block:: python

    translated_name = product.translated.name

.. note:: Translated property will be returned if there is a ``ModelTranslation`` with the same ``language_code`` as a user's currently active language. Otherwise, the original property will be returned.
