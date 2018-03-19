Navigation
==========

Saleor gives a possibility to configure storefront navigation. It can be done in dashboard ``Navigation`` tab.

You can add up to 3 levels of menu items inside every menu you create. Each menu item can point to an internal page with Category, Collection or Page, or an external website by passing an extra URL.


Rendering
---------

Menu is rendered in templates by passing to a ``menu`` templatetag a menu slug, as shown below.

.. code-block:: html

  {% menu 'footer' %}

Menu is rendered as a vertical list by default. You can change it by passing an extra ``horizontal=True`` argument.

By default, storefront template renders menu with slug ``navbar`` as a main navigation bar and with slug ``footer`` as a footer menu.
