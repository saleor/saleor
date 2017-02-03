Product management
==================

Before filling your shop with products we need to introduce 3 product concepts - *product classes*, *products*, *product variants*.

**Example:** Book store - one of *products* would be "Introduction to Saleor". The book is available in hard and soft cover, so there would be 2 *product variants*. Type of cover is only attribute which creates separate variants in our store, so we use *product class* named "Book" with activated variants and 'Cover type' variant attribute.

Class diagram
-------------

.. image:: img/product_class_tree.png

Product variant
---------------

It's most important object in shop. All cart and stock operations use variants. Even if your *product* don't have multiple variants, we create one under the hood.

Product
-------

Describes common details of few *product variants*. When shop displays category view, items on the list are distinct *products*. If variant has no overrode property (example: price), default value is taken from *product*.

- available_on
    Until this date product is not listed in storefront and is unavailable for users.

- is_featured
    Featured products are displayed on front page.


Product class
-------------

Think about it as template for your *products*. Multiple *products* can use same *product class*.
Note: In interface product class is called *Product Type*

- product_attributes
    Attributes shared with all *product variants*. Example: Publisher - all book variants are published by same company

- variant_attributes
    It's what distinguishes different *variants*. Example: Cover type - your book can be in hard or soft cover.

- is_shipping_required
    Mark as false for *products* which does not need shipping. Could be used for digital products.

- has_variants
    If your *product* has no different variants or if you want to create separate *product* for every one of them - turn this option off.
    Note: this option simplifies dashboard. There is always *variant* created under the hood.


.. warning::
    Changing a *product class* affects all *products* of this class.

.. warning::
    You can't remove *product class* if it has any *products*.


Attributes
----------

*Attributes* can help you better describe your products. Also, the can be used to filter items in category views.
There are 2 types of *attributes* - choice type and text type. If you don't provide choice values, then attribute is text type.

**Examples**

* *Choice type*: Every shirt you sell can be made in 3 colors. Then you create *attribute* Color with 3 choice values (for example 'Red', 'Green', 'Blue')
* *Text type*: Number of pages


Example - Coffee
----------------

Your shop sells Coffee from around the world. Customer can order 1kg, 500g and 250g packages. Orders are shipped by couriers.

**Attributes**

===================  ==================
 *Name*               *Values*
-------------------  ------------------
Country of origin     Brazil, Vietnam, Colombia, Indonesia
Package size          1kg, 500g, 250g
===================  ==================

**Product class**

========================  =================
*Name*                    Coffee
*Product Attributes*      Country of origin
*Variant Attributes*      Package size
*Has variants*            Yes
*Is shipping required*    Yes
========================  =================

**Product**

=============================  =================================
*Product class*                Coffee
*Name*                         Best Java Coffee
*Country of Origin attribute*  Indonesia
*Description*                  Best coffee found on Java island!
=============================  =================================

**Variants**

========================  =======
*Package size attribute*  *Price*
1kg                        $20
500g                       $12
250g                       $7
========================  =======


Example - Online game item
--------------------------

You have great selection of online games items. Each item is unique, important details are included in description. Bought items are shipped directly to buyer account.

**Attributes**

==========  =====================================
*Name*      *Values*
Game        Kings Online, War MMO, Target Shooter
Max attack  ---
==========  =====================================


**Product class**

======================  ================
*Name*                  Game item
*Product Attributes*    Game, Max attack
*Variant Attributes*    None
*Has variants*          No
*Is shipping required*  No
======================  ================

**Product**

===============  ================  =======  ================  ======================  =======================================================
*Product class*  *Name*            *Price*  *Game attribute*  *Max attack attribute*  *Description*
Game item        Magic Fire Sword  $199     Kings Online      8000 damage             Unique sword for any fighter. Set your enemies in fire!
Game item        Rapid Pistol      $2500    Target Shooter    250 damage              Fastest pistol in whole game.
===============  ================  =======  ================  ======================  =======================================================
