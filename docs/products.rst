Product management
==================

Before filling your shop with products we need to introduce 3 product concepts - ProductClass, Product, ProductVariant.

**Example:** Book store - one of Products would be "Introduction to Saleor". Book is available in hard and soft cover, so there would be 2 ProductVariants. Type of cover is only attribute which creates separate variants in our store, so we use ProductClass named "Book" with activated variants and 'Cover type' variant attribute.


ProductVariant
--------------

It's most important object in shop. All cart and stock operations use variants. Even if your Product don't have multiple variants, we create one under the hood.

Product
-------

Describes common details of few ProductVariants. When shop displays category view, items on the list are distinct Products. If variant has no overrode property (example: price), default value is taken from Product.


ProductClass
------------

Think about it as template for your products. You can describe here attributes and change number of variants.

**Warning:** Changing ProductClass has effect on all created with it Products.

**Warning:** You can't remove ProductClass if it has any Products.
