Product management
==================

Before filling your shop with products we need to introduce 3 product concepts - *product classes*, *products*, *product variants*.

**Example:** Book store - one of *products* would be "Introduction to Saleor". The book is available in hard and soft cover, so there would be 2 *product variants*. Type of cover is only attribute which creates separate variants in our store, so we use *product class* named "Book" with activated variants and 'Cover type' variant attribute.


Product variant
---------------

It's most important object in shop. All cart and stock operations use variants. Even if your *product* don't have multiple variants, we create one under the hood.

Product
-------

Describes common details of few *product variants*. When shop displays category view, items on the list are distinct *products*. If variant has no overrode property (example: price), default value is taken from *product*.


Product class
-------------

Think about it as template for your products. You can describe here attributes and change number of variants.

.. warning::
    Changing a *product class* affects all *products* of this class.

.. warning::
    You can't remove *product class* if it has any *products*.
